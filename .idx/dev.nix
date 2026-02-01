# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "unstable"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    (pkgs.python311.withPackages (ps: [
      ps.pydantic
      ps.pyarrow
      ps.sqlalchemy
      # ps.ccxt # Temporarily removed due to build issues
      ps.pyyaml
      ps.numpy
      ps.pandas
      ps.pytest
    ]))
  ];

  # Folders to add to PATH
  # path = [
  #   "bin"
  #   ".local/bin"
  # ];

  # Environment variables
  # env = {
  #   "VAR" = "value";
  # };

  # Scripts to run on workspace startup
  # startup = {
  #   # "example" = {
  #   #   "command" = "echo 'Hello, world!'";
  #   #   "background" = false;
  #   # };
  # };

  # Ports to expose
  # ports = {
  #   "Vite" = 3000;
  # };
}
