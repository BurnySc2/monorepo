## Login
```mermaid
---
title: Login flow
---
graph LR;
    A["/"login]-->B[Login with twitch];
    A-->C[Login with github];
    A-->D[Login with facebook];
    A-->E[Login with google];
```
