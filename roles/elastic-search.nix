{ ... }: {
  boot.kernel.sysctl."vm.max_map_count" = 262144;
}
