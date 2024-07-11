from grit import Variation

class Environment(Variation):
  var1: str = "lalala"

# class Turn(Variation):
#   pass

# class Taste(Variation):
#   pass

# class Animal(Variation):
#   pass

Environment(name="dev")
Environment(name="dev-nab")
Environment(name="qa", var1="lololo")
Environment(name="test")
Environment(name="prod")

# Turn(name="first")
# Turn(name="second")
# Turn(name="third")

# Taste(name="sweet")
# Taste(name="sour")

# Animal(name="rabbit")
# Animal(name="donkey")
# Animal(name="turtle")
# Animal(name="rat")