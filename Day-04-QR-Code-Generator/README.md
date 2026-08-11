# Day 04 - QR Code Generator

This beginner-friendly Python project creates a real QR code image from short text or a short URL.

The program does not need any external package. It creates a small Version 1 QR code and saves it as an `.svg` image file that opens in a browser.

## What You Learn

- How to take user input with `input()`
- How to organize code with functions
- How text can be converted into bits
- How a simple image file can be written from Python

## Limits

This simple project supports up to 17 UTF-8 bytes of text, which is enough for short words and small URLs.

Examples:

```text
Hello
OpenAI
https://x.ai
```

## How to Run

```bash
python main.py
```

Then enter the text you want to encode and the output file name.

If you leave the file name blank, the program saves the image as:

```text
qr_code.svg
```

You can open the `.svg` file in Chrome, Edge, Firefox, or any modern browser.

## Example

```text
Simple QR Code Generator
Enter short text or a short URL. Maximum: 17 UTF-8 bytes.
Text to encode: Hello
Output file name (default: qr_code.svg): hello_qr
Done! Your QR code was saved as hello_qr.svg.
```
