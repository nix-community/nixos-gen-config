{
  description = "Python application managed with poetry2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    flake-utils = { url = "github:numtide/flake-utils"; };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ poetry2nix.overlay ];
        };

        python = pkgs.python39;
        projectDir = ./.;
        overrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
          # Python dependency overrides go here
          pyudev = super.pyudev.overridePythonAttrs (oldAttrs: {
            postPatch = ''
              substituteInPlace src/pyudev/_ctypeslib/utils.py \
                --replace "find_library(name)" "'${super.pkgs.lib.getLib super.pkgs.systemd}/lib/libudev.so'"
            '';
          });
          icecream = super.icecream.overridePythonAttrs (oldAttrs: {
            #  # i don't know why the thing below is required when the package in nixpkgs works fine
            #  # ERROR: Could not find a version that satisfies the requirement executing>=0.3.1 (from icecream) (from versions: none)
            #  # ERROR: No matching distribution found for executing>=0.3.1
            postPatch = ''
              substituteInPlace setup.py --replace 'executing>=0.3.1' 'executing<0.3.1'
            '';
          });
          typing-extensions = super.typing-extensions.overridePythonAttrs (oldAttrs: {
            format = "flit";
          });
        });

        packageName = "nixos-gen-config";
      in
      {

        packages.${packageName} = pkgs.poetry2nix.mkPoetryApplication {
          inherit python projectDir overrides;
          preBuild = ''
        '';
          # Non-Python runtime dependencies go here
          buildInputs = with pkgs; [ udev ];
          propagatedBuildInputs = with pkgs; [ udev ];
        };

        defaultPackage = self.packages.${system}.${packageName};

        devShell = pkgs.mkShell {
          buildInputs = [
            (pkgs.poetry2nix.mkPoetryEnv {
              inherit python projectDir overrides;
            })
            pkgs.python39Packages.poetry
          ];
        };

      });
}
