# Third-party data notice

## GeoNames postal code data

`ES.txt` is the Spain extract of the [GeoNames](https://www.geonames.org) postal code dataset:

- Source: https://download.geonames.org/export/zip/ES.zip
- Licence: [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)

The GeoNames postal code readme (https://download.geonames.org/export/zip/readme.txt) states, verbatim:

> This work is licensed under a Creative Commons Attribution 4.0 License.
> This means you can use the dump as long as you give credit to geonames (a link on your website to www.geonames.org is ok)

That statement was checked against the live readme on 2026-11-25.

**Credit:** Postal code data © [GeoNames](https://www.geonames.org), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

### Accuracy

The same readme says that for many countries the latitude and longitude are determined by an
algorithm that searches the place names in the main GeoNames database, so they are approximations.
`oficina_cercana.py` further averages the coordinates of a postal code that appears in several
localities; `--precision` reports how spread out those localities are.

## This project's own licence

This repository has no licence file for its own code yet. That choice is up to the repository owner
and is not covered by this notice, which only concerns the GeoNames data.
