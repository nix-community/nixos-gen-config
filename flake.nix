{
  description = "Python application managed with poetry2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    poetry2nix = {
      url = "github:artturin/poetry2nix/addoverrides1";
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
              extraPackages = (ps: with ps; [
                (toPythonModule (pkgs.util-linux.overrideAttrs (oldAttrs: { nativeBuildInputs = oldAttrs.nativeBuildInputs ++ [ pkgs.python3 ]; })))
              ]);
            })
            pkgs.python39Packages.poetry
          ] ++ (with pkgs.python39Packages; [
            black
            flake8
            flake8-length
            mypy
            pylint
          ]);
        };

      });
}
