{ pkgs, config, ... }:
let
  c = config.settings.theme.withHashTag;
in
{
  xdg.configFile."tms/config.toml".text = ''
[[search_dirs]]
path = "/home/shaw/Projects"
depth = 10

[picker_colors]
highlight_color = "${c.base01}"
highlight_text_color = "${c.base05}"
  '';

  programs.tmux = {
    enable = true;
    baseIndex = 1;
    keyMode = "vi";
    # sensible adds some config I don't like if I set the shortcut here
    #shortcut = "j";
    terminal = "tmux-256color";
    escapeTime = 0;
    extraConfig = builtins.readFile ./tmux.conf;

    plugins = with pkgs.tmuxPlugins; [
      yank
      open
      copycat
      fingers
      sessionist
      vim-tmux-navigator
    ];
  };
}
