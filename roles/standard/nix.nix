{ pkgs, ... }:
{
  nix = {
    nixPath = import ../../nix-path.nix;
    trustedUsers = [ "@wheel" ];
    # Automatically optimize the Nix store to save space by hard-linking
    # identical files together. These savings add up.
    autoOptimiseStore = true;
    # keep-* for nix-direnv nix-shell generations
    extraOptions = ''
      keep-outputs = true
      keep-derivations = true
      experimental-features = nix-command flakes
    '';
    binaryCaches = [ "https://hydra.iohk.io" "https://iohk.cachix.org" ];
    binaryCachePublicKeys = [ "hydra.iohk.io:f/Ea+s+dFdN+3Y/G+FDgSq+a5NEWhJGzdjvKNGv0/EQ=" "iohk.cachix.org-1:DpRUyj7h7V830dp/i6Nti+NEO2/nhblbov/8MW7Rqoo=" ];
  };
}
