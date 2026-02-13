# WynnSource Item Encoding Schema

This is a definition for how each item in WynnCraft is represented in our data structure.
We will describe the schema in `protobuf` which can be used to generate library for multiple languages.

## Supported Item Types
- [x] Gears
  - [x] IdentifiedGear
  - [x] UnidentifiedGear
  - [x] CraftedGear
- [x] Consumables
  - [x] Crafted
    - [x] Potion
    - [x] Food
    - [x] Scroll
  - [x] NonCrafted
    - [x] Potion
    - [x] FixedConsumable (e.g. Speed Surge)
- [x] Material
- [x] Ingredient
- [x] Tome
- [x] Charm
- [x] Aspect
- [x] Rune
- [x] DungeonKey
- [x] CrafterBag
- [x] Trinket
- [x] Mounts
  - [x] Horse
- [x] TeleportationScroll
- [x] Corkians
  - [x] CorkianAmplifier
  - [x] CorkianSimulator
  - [x] CorkianInsulator
- [x] Emeralds
  - [x] LiquidEmerald
  - [x] EmeraldBlock
  - [x] Emerald
- [x] EmeraldPouch
- [x] NamedItem (e.g. Quest Items, Ability Shards, etc.)


## Mappings

[Identification Mapping]()
[Shiny Mapping]()

## Contribution
We use [buf](https://github.com/bufbuild/buf) to manage our protobuf schema.
We use [prek](https://github.com/j178/prek) to install and run pre-commit hooks.

Before contributing, please make sure to install the pre-commit hooks by running `prek install` in the root directory of this repository.