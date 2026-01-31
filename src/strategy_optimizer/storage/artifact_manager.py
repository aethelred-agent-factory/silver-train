import logging
import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


class ArtifactManager:
    """
    Manages object storage (local filesystem or S3) for immutable artifacts,
    including checksum verification.
    """

    def __init__(self, config, crypto_utils):
        self.config = config
        self.crypto_utils = crypto_utils
        self.local_artifact_path = Path(config["system_config"]["paths"]["artifacts"])
        self.local_artifact_path.mkdir(parents=True, exist_ok=True)

        self.s3_bucket = os.getenv("S3_BUCKET")
        self.use_s3 = bool(self.s3_bucket)

        if self.use_s3:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
                    aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
                )
                logging.info(
                    f"Initialized ArtifactManager with S3 bucket: {self.s3_bucket}"
                )
            except Exception as e:
                logging.error(
                    f"Failed to initialize S3 client: {e}. Falling back to local storage."
                )
                self.use_s3 = False
        else:
            logging.info(
                f"Initialized ArtifactManager with local storage: {self.local_artifact_path}"
            )

    def upload_artifact(self, data: str, artifact_id: str) -> str:
        """
        Uploads an artifact (string data) to storage, saves its checksum, and returns its URI.
        """
        data_bytes = data.encode("utf-8")
        checksum = self.crypto_utils.sha256_hash(data_bytes)

        if self.use_s3:
            try:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=artifact_id,
                    Body=data_bytes,
                    Metadata={"checksum": checksum},
                )
                uri = f"s3://{self.s3_bucket}/{artifact_id}"
                logging.info(f"Uploaded {artifact_id} to S3.")
                return uri, checksum
            except ClientError as e:
                logging.error(
                    f"Failed to upload {artifact_id} to S3: {e}. Saving locally as fallback."
                )

        # Local storage (or fallback)
        file_path = self.local_artifact_path / artifact_id
        file_path = file_path.resolve()  # Convert to absolute path
        with open(file_path, "wb") as f:
            f.write(data_bytes)
        with open(file_path.with_suffix(file_path.suffix + ".sha256"), "w") as f:
            f.write(checksum)
        uri = file_path.as_uri()
        logging.info(f"Saved {artifact_id} to local storage.")
        return uri, checksum

    def download_artifact(self, artifact_id: str) -> tuple[str, str]:
        """
        Downloads an artifact and its checksum.
        Returns a tuple of (artifact_content_string, stored_checksum_string).
        """
        data_bytes = None
        stored_checksum = None

        try:
            if self.use_s3:
                response = self.s3_client.get_object(
                    Bucket=self.s3_bucket, Key=artifact_id
                )
                data_bytes = response["Body"].read()
                stored_checksum = response["Metadata"].get("checksum")
            else:
                file_path = self.local_artifact_path / artifact_id
                checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
                if file_path.exists():
                    with open(file_path, "rb") as f:
                        data_bytes = f.read()
                    if checksum_path.exists():
                        with open(checksum_path, "r") as f:
                            stored_checksum = f.read().strip()
        except Exception as e:
            logging.error(f"Failed to download artifact {artifact_id}: {e}")
            return None, None

        if data_bytes and stored_checksum:
            # Verify checksum
            computed = self.crypto_utils.sha256_hash(data_bytes)
            if computed != stored_checksum:
                logging.error(
                    f"Checksum mismatch for artifact {artifact_id}: expected {stored_checksum}, got {computed}"
                )
                return None, None
            return data_bytes.decode("utf-8"), stored_checksum
        elif data_bytes:
            logging.warning(f"No checksum found for artifact {artifact_id}.")
            return data_bytes.decode("utf-8"), None

        return None, None

    def get_artifact_uri(self, artifact_id: str) -> str:
        """Returns the storage URI for a given artifact ID."""
        if self.use_s3:
            return f"s3://{self.s3_bucket}/{artifact_id}"
        else:
            return (self.local_artifact_path / artifact_id).as_uri()
