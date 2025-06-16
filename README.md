# competitive-landscape

This repo contains a website that generates a competitive landscape, given an input of the company name and URL.

It uses OpenAI's o3-pro model to find the names of the competitors and Clay to fill out the rest of the information.

The website used to be hosted using Render. But they have a very silly feature that pauses your website if the user has been idle for 15 minutes. Sometimes the o3-pro query takes this long to run. This doesn't stop the code that's actively running, but it really looks like it does to non-technical people.

So, I moved to hosting on fly instead. So far it's a significantly superior service, for free users building small apps. I'm leaving the render.yaml file in here to remind people not to use their service, because I'm petty like that.
