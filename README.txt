This project belongs to a project of two micro services:
1. Collect data from an internet page and store in redis
2. Show the data from redis on an raspberry zero with an e-paper display attached.

Here you get part two of this project.

Precondition:
=============
- A redis data base must be available and some data must be stored.
- The access to redis is in src/rpb.e-paper.showdata.config of the structure:
[redis]
rhost=<hostname of redis server>
password=<password  for redis server>

The file is encrypted with git-crypt.

Short description:
==================
Data is read in redis from the keys:
- NewLog:<epoch>
- World
- <Country> where <Country> is taken from "NewLog:<epoch>"

Data is shown on the display for:
- World
- For each country found in "NewLog:<epoch>"

The display is updated after 300 secs.

