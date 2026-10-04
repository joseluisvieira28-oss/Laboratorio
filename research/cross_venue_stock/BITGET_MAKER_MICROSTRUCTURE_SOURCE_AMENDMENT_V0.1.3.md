# BITGET MAKER MICROSTRUCTURE SOURCE V0.1.3 — DOWNLOAD HELPER RESOLUTION

Date: 2026-10-05

V0.1.2 established that public historical trades are accessible for all four frozen candidates, while no concrete historical depth file/API URL had yet been proven.

V0.1.3 is still source-only. It:
- scans every JavaScript bundle referenced by Bitget's official data-download page;
- records contexts around getDownloadFiles, fileUrl, fileName, downloadFile and related strings;
- records nearby webpack module references and route-like strings solely to resolve the official file-download transport.

It does not:
- join signals to market outcomes;
- classify fills;
- simulate queue position;
- compute PnL;
- change the frozen candidate set or burned source date.

Historical depth remains unproven until a concrete retrievable file/API transport is identified.
