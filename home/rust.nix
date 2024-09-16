{ pkgs, ... }:
let
  rustBinDir = "$HOME/.local/share/cargo/bin";
in
{
  home.packages = [
    pkgs.bacon
    pkgs.cargo
    pkgs.cargo-edit
    pkgs.cargo-watch
    pkgs.clippy
    pkgs.rustc
  ];

  home.sessionPath = [ rustBinDir ];
}
