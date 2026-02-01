# https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  channel = "unstable";

  packages = [
    pkgs.python311

    # Testing
    pkgs.python311Packages.pytest
    pkgs.python311Packages.pytest-asyncio

    # Core libs
    pkgs.python311Packages.pydantic
    pkgs.python311Packages.pyarrow
    pkgs.python311Packages.sqlalchemy
    pkgs.python311Packages.pyyaml
    pkgs.python311Packages.numpy
    pkgs.python311Packages.pandas
    pkgs.python311Packages.aiohttp
    pkgs.python311Packages.python-dotenv
    pkgs.python311Packages.cryptography
    pkgs.python311Packages.scipy
    pkgs.python311Packages.requests
    pkgs.python311Packages.fastapi
    pkgs.python311Packages.uvicorn
    pkgs.python311Packages.prometheus-client
    pkgs.python311Packages.boto3

    # Native runtime support
    pkgs.stdenv.cc.cc.lib
  ];

  env = {
    PYTHONUNBUFFERED = "1";
  };
}