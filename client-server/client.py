import Pyro4

name=input("What is your name?")

greeting_maker=Pyro4.Proxy("PYRONAME:example.greeting")
print(greeting_maker.get_fortune(name))
