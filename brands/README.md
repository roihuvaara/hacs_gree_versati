# Brand icons for home-assistant/brands

Home Assistant (and HACS) show integration icons from
<https://github.com/home-assistant/brands>, not from the integration itself.
Until the `gree_versati` domain is added there, the integration shows a
generic placeholder icon.

The `gree_versati/` folder here contains the Gree brand icon (taken from the
existing core `gree` brand at <https://brands.home-assistant.io/gree/>) in the
layout the brands repo expects:

```
custom_integrations/gree_versati/icon.png      (256x256)
custom_integrations/gree_versati/icon@2x.png   (512x512)
```

To submit:

1. Fork <https://github.com/home-assistant/brands>.
2. Copy `brands/gree_versati/` into `custom_integrations/gree_versati/`.
3. Open a PR. Once merged, the icon appears at
   `https://brands.home-assistant.io/gree_versati/icon.png` and Home Assistant
   picks it up automatically — no changes needed in this repository.
