Dependencies: -netmiko 
	      -nornir 
	      -sqlite3

Important:Make sure you have configured a static route from your computer to the device loopback 
interface on the switch ( 1.1.1.1 ) that is used for management 
	  Also change the ip address on the eth 0/0 interface on the switch to whatever network 
you may NAT ( in mine case is saved as 192.168.122.0 /24 , your could be different) 


		
