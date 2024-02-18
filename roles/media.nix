{ ... }:
{
  services.sonarr = {
    enable = true;
    openFirewall = true;
  };

  services.radarr = {
    enable = true;
    openFirewall = true;
  };

  services.transmission = {
    enable = true;
    openPeerPorts = true;
    openRPCPort = true;
    settings = {
      rpc-bind-address = "0.0.0.0";
    };
  };
}

