{ pkgs, config, ... }:
let
  c = config.my.theme.withHashTag;
in
{
  xdg.configFile."tms/config.toml".text = ''
[[search_dirs]]
path = "${config.home.homeDirectory}/Projects"
depth = 10

[picker_colors]
highlight_color = "${c.base01}"
highlight_text_color = "${c.base05}"

[shortcuts]
"ctrl-y" = "confirm"
  '';

  programs.tmux = {
    enable = true;
    baseIndex = 1;
    keyMode = "vi";
    shortcut = "j";
    terminal = "tmux-256color";
    escapeTime = 0;
    sensibleOnTop = true;
    plugins = with pkgs.tmuxPlugins; [
      yank
      open
      copycat
      fingers
      sessionist
      vim-tmux-navigator
    ];
    extraConfig = builtins.readFile ./tmux.conf;
  };
}
