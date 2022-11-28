# GNSSR 4 Water 
## What is gnssr4water?
This repository is a fork of the [gnssr4river](https://github.com/lroineau/gnssr4river), which originated from an internship of [Lubin Roineau](https://github/lroineau) under supervision of Roelof Rietbroek at the Water Resources Department at the University of Twente.

gnssr4water is a free and open-source Python toolbox that helps to:
- find suitable locations and antenna heigths for placing a low-cost GNSS receiver to perform GNSS reflectometry over rivers and lakes.
- assess rivers stages height using the logged SNR data (Signal-to-Noise Ratio)

## Documentation and examples

A Notebook example that explains the different features of the toolbox can be found [here](docs/example.ipynb). It countains basics example of every function. 

Another Notebook ready to use can be found [here](docs/guideline.ipynb). It aims to provide various information for a given location, including the reflection points, the optimal height of the antenna, and potential additional data such as intersection with rivers and altimeter tracks.

## How to use it

You can use gnssr4water by cloning it with a bash terminal:
```
git clone https://github.com/ITC-Water-Resources/gnssr4water.git
```
or (when using ssh):
```
git clone git@github.com:ITC-Water-Resources/gnssr4water.git
```


## How should I setup a low-cost GNSS-reflectometer?
Please have a look at the following repositories:
* [gnssr-raspberry](https://github.com/ITC-Water-Resources/gnssr-raspberry)
* [actinius-gnssr](https://github.com/ITC-Water-Resources/actinius-gnssr)


## Contributors
* **Lubin Roineau** (Original Author) [lubin_roineau](https://github.com/lroineau/)
* **Roelof Rietbroek**
* ...


## Further reading/other sources
* [Kristine Larsson's gnss-reflectometry tools](https://github.com/kristinemlarson/gnssrefl)
* [Makan Karegar's  rapsberry based gnss reflectometer](https://github.com/MakanAKaregar/RPR)
* [Felipe Geremia-Nievinski feather gnss-reflectometer](https://github.com/fgnievinski/mphw)
