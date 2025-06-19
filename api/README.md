# Latin Macronizer API

This API provides an endpoint to macronize Latin text using the underlying macronizer engine.

## Endpoint: `POST /api/macronize`

Processes Latin text and applies macronization based on the provided options.

**Request Method:** `POST`

**Content-Type:** `application/json`

### Request Body

The request body must be a JSON object with the following fields:

-   `text_to_macronize` (string, **required**): The Latin text you want to process.
    -   Example: `"Arma virumque cano, Troiae qui primus ab oris."`
-   `domacronize` (boolean, optional, default: `true`): If `true`, marks long vowels.
-   `alsomaius` (boolean, optional, default: `false`): If `true`, also marks vowels in words like "māius".
-   `scan_option_index` (integer, optional, default: `0`): The index corresponding to the desired scansion option. The available options can be inferred from the `SCANSIONS` list in `macronizer.py`. Index `0` typically means no scansion.
    -   Example: `0` for prose, `1` for Dactylic Hexameter (refer to `SCANSIONS` in `macronizer.py` for exact indices and descriptions).
-   `performitoj` (boolean, optional, default: `false`): If `true`, converts appropriate 'i' characters to 'j'.
-   `performutov` (boolean, optional, default: `false`): If `true`, converts appropriate 'u' characters to 'v'.

### Success Response (200 OK)

If successful, the API returns a JSON object with the following structure:

```json
{
  "macronized_text": "Ārma virumque canō, Trōiae quī prīmus ab ōrīs.",
  "original_text": "Arma virumque cano, Troiae qui primus ab oris.",
  "options_used": {
    "domacronize": true,
    "alsomaius": false,
    "scan_option_index": 1,
    "scan_description": "Dactylic Hexameter",
    "performitoj": false,
    "performutov": false
  }
}
```

-   `macronized_text` (string): The processed text with macrons applied (or other transformations).
-   `original_text` (string): The original text submitted.
-   `options_used` (object): An object detailing the options that were effectively used for processing the request, including a description of the scansion option if one was selected.

### Error Responses

-   **400 Bad Request:** If the request is malformed (e.g., invalid `scan_option_index`). The response body will contain a `detail` field with more information.
    ```json
    {
      "detail": "Invalid scan_option_index. Must be less than N."
    }
    ```
-   **422 Unprocessable Entity:** If the request body is not valid JSON or misses required fields (FastAPI default).
-   **500 Internal Server Error:** If an unexpected error occurs during processing on the server. The response body may contain a `detail` field.

### Example `curl` Request

```bash
curl -X POST "YOUR_VERCEL_DEPLOYMENT_URL/api/macronize" \
     -H "Content-Type: application/json" \
     -d '{
           "text_to_macronize": "Gallia est omnis divisa in partes tres.",
           "domacronize": true,
           "scan_option_index": 0
         }'
```

Replace `YOUR_VERCEL_DEPLOYMENT_URL` with the actual URL of your Vercel deployment.
