
{ pkgs ? import <nixpkgs> {} }:

let
  ccxt = pkgs.python3Packages.buildPythonPackage rec {
    pname = "ccxt";
    version = "4.5.35";

    src = pkgs.fetchPypi {
      inherit pname version;
      sha256 = "sha256-uUnxXKJwkBaDt/MqsrXPmqXkReEt7deSah+hzZl1fEA=";
    };

    preConfigure = ''
      touch README.md
    '';

    postPatch = ''
      find . -type f -name "*.py" -exec sed -i "s/from  import/from .common import/g" {} + 
    '';

    propagatedBuildInputs = with pkgs.python3Packages; [
      setuptools
      certifi
      cryptography
      aiohttp
      aiodns
      yarl
      coincurve
    ];
    doCheck = false;
  };

  openai = pkgs.python3Packages.buildPythonPackage rec {
    pname = "openai";
    version = "1.12.0";
    format = "pyproject";

    src = pkgs.fetchPypi {
      inherit pname version;
      sha256 = "sha256-mcXSV9CeplM9aJ0cx3yqCsZ5+iHv74iT2LCDKoaHfxs=";
    };

    propagatedBuildInputs = with pkgs.python3Packages; [
      anyio
      distro
      httpx
      pydantic
      sniffio
      tqdm
      typing-extensions
      hatchling
    ];
    doCheck = false;
  };

  pythonPackages = ps: with ps; [
    pyarrow
    sqlalchemy
    pyyaml
    numpy
    pandas
    scipy
    requests
    python-dotenv
    fastapi
    uvicorn
    prometheus-client
    boto3
    rich
    blessed
  ] ++ [ ccxt openai ];

  pythonWithPackages = pkgs.python3.withPackages pythonPackages;
in

pkgs.mkShell {
  buildInputs = [
    pythonWithPackages
    pkgs.stdenv.cc.cc.lib
  ];

  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
  '';
}
