# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
    config.vm.box = "ubuntu/bionic64"

    config.vm.network "forwarded_port", guest: 8000, host: 8000

    config.vm.synced_folder ".", "/home/vagrant/demozoo"

    config.vm.provider "virtualbox" do |vb|
        vb.memory = "1024"
    end

    config.vm.provision :shell, :path => "etc/vagrant-provision.sh"
end
