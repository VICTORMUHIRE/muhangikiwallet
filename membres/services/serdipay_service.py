import os
import requests
import json
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout

from dotenv import load_dotenv

load_dotenv() 

class SerdiPayService:
    def __init__(self):
        
        self.TOKEN_URL = os.getenv('SERDIPAY_TOKEN_URL') 
        self.C2B_URL = os.getenv('SERDIPAY_C2B_URL')   
        self.B2C_URL = os.getenv('SERDIPAY_B2C_URL') 
        
        self.USERNAME = os.getenv('SERDIPAY_USERNAME')   
        self.PASSWORD = os.getenv('SERDIPAY_PASSWORD')   
        self.PIN = os.getenv('SERDIPAY_PIN')             
        self.API_ID = os.getenv('SERDIPAY_API_ID')       
        
        self.MERCHANT_CODE = os.getenv('SERDIPAY_MERCHANT_CODE')       
        
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
            
            if not response.ok: 
                error_message_from_api = "Une erreur inconnue est survenue lors de la récupération du token."
                try:
                    error_data = response.json()
                    
                    if 'message' in error_data and error_data['message']:
                        error_message_from_api = error_data['message']
                    
                    elif 'detail' in error_data and error_data['detail']:
                        error_message_from_api = error_data['detail']
                    else:                        
                        error_message_from_api = f"Réponse d'erreur SerdiPay sans message spécifique (Statut: {response.status_code})."
                except json.JSONDecodeError:
                    
                    error_message_from_api = f"Erreur de réponse SerdiPay (Statut: {response.status_code}). Le corps de la réponse n'était pas un JSON valide ou était vide."
                    
                    if response.text:
                        error_message_from_api += f" Corps: '{response.text[:200]}...'" 
                except Exception as e_parse:                    
                    error_message_from_api = f"Erreur inattendue lors de l'analyse de la réponse d'erreur SerdiPay (Statut: {response.status_code}, Erreur de parsing: {e_parse})."
                
                raise SerdiPayServiceError(f"Échec de l'authentification SerdiPay: {error_message_from_api}")
                        
            data = response.json()
            token = data.get('access_token')

            if not token:                
                raise ValueError(f"Token d'accès non reçu de SerdiPay. Réponse complète: {data}")
            
            self._access_token = token
            return token

        except ConnectionError as e:            
            raise SerdiPayServiceError(f"Échec de connexion au serveur SerdiPay pour le token. Vérifiez votre connexion internet ou l'URL du service: {e}")
        except Timeout as e:            
            raise SerdiPayServiceError(f"Délai d'attente dépassé lors de la récupération du token SerdiPay. Le serveur ne répond pas à temps: {e}")
        except RequestException as e:            
            
            raise SerdiPayServiceError(f"Erreur réseau ou HTTP inattendue lors de la récupération du token SerdiPay: {e}")
        except json.JSONDecodeError:            
            raise SerdiPayServiceError("Réponse JSON invalide de SerdiPay lors de la récupération du token. La réponse du succès n'était pas du JSON valide.")
        except ValueError as e: 
            raise SerdiPayServiceError(f"Erreur de données de token SerdiPay: {e}")
        except Exception as e:            
            raise SerdiPayServiceError(f"Une erreur système inattendue est survenue lors de la récupération du token SerdiPay: {e}")

    def recharge_account_c2b(self, client_phone, amount, currency, telecom_provider):
        """
        Effectue un rechargement C2B (Customer to Business) via SerdiPay.
        Le client paie le compte du marchand.
        """
        # Ces vérifications initiales sont bonnes, mais elles peuvent être centralisées dans __init__
        # si vous préférez, comme dans l'exemple __init__ ci-dessus.
        # Sinon, assurez-vous que toutes les vérifications nécessaires sont là.
        if not self.MERCHANT_CODE:
            raise SerdiPayServiceError("Le code marchand SerdiPay (SERDIPAY_MERCHANT_CODE) n'est pas configuré.")
        if not self.API_ID:
            raise SerdiPayServiceError("L'ID API SerdiPay (SERDIPAY_API_ID) n'est pas configuré.")
        if not self.PIN:
            raise SerdiPayServiceError("Le PIN marchand SerdiPay (SERDIPAY_PIN) n'est pas configuré.")
        if not self.C2B_URL:
            raise SerdiPayServiceError("L'URL C2B SerdiPay (SERDIPAY_C2B_URL) n'est pas configurée.")
        if not self.PASSWORD: # Le mot de passe est utilisé dans le payload
            raise SerdiPayServiceError("Le mot de passe SerdiPay (SERDIPAY_PASSWORD) n'est pas configuré.")


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
            "api_password": self.PASSWORD, # Assurez-vous que self.PASSWORD est bien chargé
            "merchantCode": self.MERCHANT_CODE,
            "merchant_pin": self.PIN,
            "clientPhone": client_phone,
            "amount": amount,
            "currency": currency,
            "telecom": telecom_provider
        }

        try:
            response = requests.post(self.C2B_URL, json=payload, headers=headers, timeout=30)

            
            if not response.ok: 
                specific_error_message = f"Statut HTTP {response.status_code}."
                try:
                    error_data = response.json()
                    
                    if 'message' in error_data and error_data['message']:
                        specific_error_message = error_data['message']
                    elif 'detail' in error_data and error_data['detail']:
                        specific_error_message = error_data['detail']
                    else:
                        
                        specific_error_message = f"Réponse d'erreur SerdiPay sans message spécifique (Statut: {response.status_code}, Corps: {json.dumps(error_data, ensure_ascii=False)[:200]}...)"
                except json.JSONDecodeError:
                    
                    specific_error_message = f"Réponse d'erreur SerdiPay non JSON (Statut: {response.status_code}). Corps: '{response.text[:200]}...'"
                except Exception as e_parse:
                    
                    specific_error_message = f"Erreur inattendue lors de l'analyse de la réponse d'erreur SerdiPay (Statut: {response.status_code}, Erreur: {e_parse})."
                
                
                raise SerdiPayServiceError(f"Échec du rechargement C2B: {specific_error_message}")           

            return response.json() 

        except ConnectionError as e:            
            raise SerdiPayServiceError(f"Échec de connexion au serveur SerdiPay lors du rechargement C2B. Vérifiez votre connexion internet ou l'URL du service: {e}")
        except Timeout as e:            
            raise SerdiPayServiceError(f"Délai d'attente dépassé lors du rechargement C2B SerdiPay. Le serveur ne répond pas à temps: {e}")
        except RequestException as e:                         
            raise SerdiPayServiceError(f"Erreur réseau inattendue lors du rechargement C2B SerdiPay: {e}")
        except json.JSONDecodeError:            
            raise SerdiPayServiceError("Réponse JSON invalide lors du rechargement C2B SerdiPay. La réponse attendue pour le succès n'était pas du JSON valide.")
        except Exception as e:
            
            raise SerdiPayServiceError(f"Une erreur système inattendue est survenue lors du rechargement C2B: {e}")


# Classe d'exception personnalisée pour le service SerdiPay
class SerdiPayServiceError(Exception):
    """Exception personnalisée pour les erreurs du service SerdiPay."""
    pass