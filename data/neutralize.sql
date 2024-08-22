-- disable qpaypro payment provider
UPDATE payment_provider
   SET qpaypro_llave_publica = NULL,
       qpaypro_llave_privada = NULL;