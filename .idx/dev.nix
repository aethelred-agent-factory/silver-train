# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "unstable";

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.virtualenv
    pkgs.python311Packages.pytest
    pkgs.python311Packages.pytest-asyncio
    pkgs.python311Packages.pydantic
    pkgs.python311Packages.pyarrow
    pkgs.python311Packages.sqlalchemy
    pkgs.python311Packages.pyyaml
    pkgs.python311Packages.numpy
    pkgs.python311Packages.pandas
    pkgs.python311Packages.aiohttp
    pkgs.python311Packages.python-dotenv
    pkgs.python311Packages.cryptography
  ];

  # Set environment variables
  env = {
    PYTHONPATH = "${pkgs.python311Packages.pytest}/lib/python3.11/site-packages";
  };
}