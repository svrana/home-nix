{ pkgs, lib, ... }:

{
  programs.fzf = {
    enable = true;
    defaultCommand = "fd --type f";
    defaultOptions = [
      "--reverse"
      "--info inline"
      "--bind=ctrl-f:page-down,ctrl-b:page-up,ctrl-d:page-up"
    ];
    fileWidgetCommand = "fd --type f";
  };

  programs.bash.initExtra = ''
    # open a file under the current directory
    bind -x '"\C-p": f() { local file=$(fzf -m --height 80% --reverse) && [[ -n $file ]] && $EDITOR $file ; }; f'

    # open a dotfile
    bind -x '"\C-n": f() { pushd $DOTFILES > /dev/null ; local file=$(fzf -m --height 80% --reverse) && [[ -n $file ]] && $EDITOR $file ; popd > /dev/null ; }; f'

    # open a file under the current (git) project root
    bind -x '"\C-f": f() { pushd $(git_root) > /dev/null ; local file=$(fzf -m --height 80% --reverse) && [[ -n $file ]] && $EDITOR $file ; popd > /dev/null ; }; f'
  '';
}
