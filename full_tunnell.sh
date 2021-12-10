#!/bin/bash

#echo "Insert SSH target"
#read target

target=simone@10.0.2.11

sudo ip tuntap add dev tap0 mod tap
sudo ip a a 10.100.100.100/24 dev tap0 && sudo ip link set tap0 up
conf=$(grep -R "PermitTunnel no" /etc/ssh/sshd_config)
if [ "$conf" = "" ]; then
	echo "[+] SSH TunnelPermit yes already set up. Skipping"
	else 
	echo "Updating sshd_config TunnelPermit -> yes"
	sudo sed -E -i 's/#{0,1}PermitTunnel no/PermitTunnel yes/' /etc/ssh/sshd_config
fi

echo "[+] Configuring remote host iptables"
ssh -t $target "
sudo iptables-save > iptables.conf;
sudo ip tuntap add dev tap0 mod tap;
sudo ip a a 10.100.100.101/24 dev tap0 && sudo ip link set tap0 up;
sudo bash -c 'echo 1 > /proc/sys/net/ipv4/ip_forward';
sudo iptables -t nat -A POSTROUTING -o enp0s8 -j MASQUERADE;
sudo iptables -t nat -A POSTROUTING -o tap0 -j MASQUERADE;
sudo iptables -A INPUT -i enp0s8 -m state --state RELATED,ESTABLISHED -j ACCEPT;
sudo iptables -A INPUT -i tap0 -m state --state RELATED,ESTABLISHED -j ACCEPT;
sudo iptables -A FORWARD -j ACCEPT;
"

ssh -f -N -o Tunnel=ethernet -w 0:0 $target
sudo ip route add 10.0.2.0/24 via 10.100.100.101
sudo ip route add 10.0.5.0/24 via 10.100.100.101

echo "[+] Tunnel UP: type exit to quit"
while true
do
	read press
	if [ "$press" = "exit" ]; then
	break
	else echo "Invalid option"
	fi
done

if [ "$check" = "" ]; then
	echo "[-] No need to restore sshd_config"
	else
	echo "[-] Restoring sshd_config TunnelPermit <- no"
	sudo sed -E -i 's/PermitTunnel yes/#PermitTunnel no/' /etc/ssh/sshd_config
	fi
echo "[-] Tunnel Closed"
sudo kill $(pidof ssh)
echo "[-] Clearing routes"
#sudo ip route del 10.0.2.0/24 via 10.100.100.101
sudo ip route del 10.0.5.0/24 via 10.100.100.101
sudo ip link del tap0

echo "[-] Clearing remote host iptables"
ssh -t $target "
sudo iptables-restore < iptables.conf;
sudo rm -rf iptables.conf;
sudo ip link del tap0;
"




