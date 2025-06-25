# competitive-landscape 

![Fly Deploy](https://github.com/RowanGray472/competitive-landscape/workflows/Fly%20Deploy/badge.svg)

This repo contains a website that generates a competitive landscape, given an input of the company name and URL.

It uses OpenAI's o3-pro model to find the names of the competitors, other OpenAI models to create buckets based on product type and sort the competitors,  and Clay to fill out the rest of the information (think employee count, locality, revenue, funding, etc).

I'm hosting it on [Fly](https://fly.io/). I've tried a lot of free website hosting platforms and Fly is probably the easiest to use of all of them.
