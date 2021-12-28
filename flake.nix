{
  description = "Python application managed with poetry2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils = { url = "github:numtide/flake-utils"; };
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        python = pkgs.python39;
        projectDir = ./.;
        overrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
          # Python dependency overrides go here
          icecream = super.icecream.overridePythonAttrs (oldAttrs: {
            #  # i don't know why the thing below is required when the package in nixpkgs works fine
            #  # ERROR: Could not find a version that satisfies the requirement executing>=0.3.1 (from icecream) (from versions: none)
            #  # ERROR: No matching distribution found for executing>=0.3.1
            postPatch = ''
              substituteInPlace setup.py --replace 'executing>=0.3.1' 'executing<0.3.1'
            '';
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
          propagatedBuildInputs = [ ];
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
