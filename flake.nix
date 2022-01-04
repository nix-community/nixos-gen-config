{
  description = "Python application managed with poetry2nix";

  inputs = {
    #nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs.url = "github:NixOS/nixpkgs/master";
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

        python = pkgs.python310;
        projectDir = ./.;
        overrides = pkgs.poetry2nix.overrides.withDefaults (self: super: {
          # Python dependency overrides go here
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
          checkInputs = with pkgs; [ mypy ];

          checkPhase = ''
            export MYPYPATH=$PWD/src/stubs
            mypy --strict src/nixos_gen_config
            mypy --strict tests
          '';
        };

        defaultPackage = self.packages.${system}.${packageName};

        devShell = pkgs.mkShell {
          buildInputs = [
            pkgs.pyright
            (pkgs.poetry.override { python = python; })
            (pkgs.poetry2nix.mkPoetryEnv {
              inherit python projectDir overrides;
              editablePackageSources = {
                  packageName = ./src;
              };
              extraPackages = (ps: with ps; [
                #(toPythonModule (pkgs.util-linux.overrideAttrs (oldAttrs: { nativeBuildInputs = oldAttrs.nativeBuildInputs ++ [ pkgs.python3 ]; })))
              ]);
            })
          ] ++ (with python.pkgs; [
            black
            flake8
            flake8-length
            mypy
            pylint
          ]);
          shellHook = ''
            # generate stubs with stubgen src/nixos_gen_config -o src/stubs
            export MYPYPATH=$PWD/src/stubs
            zsh
          '';
        };

      });
}
