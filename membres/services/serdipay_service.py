# your_app_name/services/serdipay_service.py (ou votre_app_name/serdipay_service.py)

import os
import requests
import json

class SerdiPayService:
    def __init__(self):
        
        self.TOKEN_URL = os.getenv('SERDIPAY_TOKEN_URL')
        self.C2B_URL = os.getenv('SERDIPAY_C2B_URL')
        self.B2C_URL = os.getenv('SERDIPAY_B2C_URL') 

        self.USERNAME = os.getenv('SERDIPAY_USERNAME')
        self.PASSWORD = os.getenv('SERDIPAY_PASSWORD')
        self.PIN = os.getenv('SERDIPAY_PIN')
        self.API_ID = os.getenv('SERDIPAY_API_ID')

        self._access_token = None

    def _get_access_token(self):
        """Récupère et renvoie un token d'accès de SerdiPay."""
        if self._access_token: 
            return self._access_token

        auth_data = {
            "email": self.USERNAME,
            "password": self.PASSWORD
        }
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(self.TOKEN_URL, json=auth_data, headers=headers, timeout=10)
            response.raise_for_status()  
            data = response.json()
            token = data.get('access_token')
            if not token:
                raise ValueError("Token d'accès non reçu de SerdiPay.")
            self._access_token = token # Cache le token
            return token
        except requests.exceptions.RequestException as e:
            raise SerdiPayServiceError(f"Erreur de connexion lors de la récupération du token SerdiPay: {e}")
        except json.JSONDecodeError:
            raise SerdiPayServiceError("Réponse JSON invalide lors de la récupération du token SerdiPay.")
        except ValueError as e:
            raise SerdiPayServiceError(f"Erreur de données lors de la récupération du token SerdiPay: {e}")

    def recharge_account_c2b(self, client_phone, amount, currency, telecom_provider):

        try:
            access_token = self._get_access_token()
        except SerdiPayServiceError as e:
            raise SerdiPayServiceError(f"Impossible d'obtenir le token pour le rechargement: {e}")

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        payload = {
            "api_id": self.API_ID,
            "api_password": self.PASSWORD, # A VERIFIER: est-ce votre mot de passe de connexion ou une autre clé?
            "merchantCode": self.USERNAME,  # A VERIFIER: est-ce l'email ou un code numérique (e.g., "466551")?
            "merchant_pin": self.PIN,
            "clientPhone": client_phone,
            "amount": amount,
            "currency": currency,
            "telecom": telecom_provider
        }

        try:
            response = requests.post(self.C2B_URL, json=payload, headers=headers, timeout=30)
            response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            # Capturer les détails de l'erreur si c'est une erreur HTTP
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                except json.JSONDecodeError:
                    error_detail = e.response.text
                raise SerdiPayServiceError(f"Erreur API SerdiPay ({e.response.status_code}): {error_detail}")
            else:
                raise SerdiPayServiceError(f"Erreur de connexion lors du rechargement SerdiPay: {e}")
        except json.JSONDecodeError:
            raise SerdiPayServiceError("Réponse JSON invalide lors du rechargement SerdiPay.")

# Classe d'exception personnalisée pour le service SerdiPay
class SerdiPayServiceError(Exception):
    """Exception personnalisée pour les erreurs du service SerdiPay."""
    pass