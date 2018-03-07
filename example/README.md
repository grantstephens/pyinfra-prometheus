# pyinfra-prometheus Example

Requirements:

+ [Vagrant](https://vagrantup.com)
+ [pyinfra](https://github.com/Fizzadar/pyinfra) >= 0.5

Boot & install the cluster:

```sh
# Bring up the VMs
vagrant up

# Deploy an prometheus cluster on them
pyinfra @vagrant deploy.py
```
