import os
from django.http import JsonResponse # Gardé au cas où, mais Django REST Framework Response est préféré dans les vues
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
        """
        Récupère et renvoie un token d'accès de SerdiPay.
        Cette méthode peut toujours lever des exceptions Python standard en cas d'échec,
        elles seront gérées par les méthodes publiques appelantes.
        """
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
                    # Tente de parser la réponse d'erreur de l'API SerdiPay
                    error_data = response.json()
                    # Si l'API renvoie un message d'erreur spécifique, utilisez-le
                    error_message_from_api = error_data.get('message', error_data) 
                except json.JSONDecodeError:                    
                    error_message_from_api = f"Erreur de réponse SerdiPay (Statut: {response.status_code}). Le corps de la réponse n'était pas un JSON valide ou était vide."
                    if response.text:
                        error_message_from_api += f" Corps: '{response.text[:200]}...'" 
                except Exception as e_parse:                        
                    error_message_from_api = f"Erreur inattendue lors de l'analyse de la réponse d'erreur SerdiPay (Statut: {response.status_code}, Erreur de parsing: {e_parse})."
                
                # Lever une exception standard ici, car c'est une méthode interne.
                # Les méthodes publiques attraperont cette exception et la convertiront en dictionnaire JSON.
                raise RequestException(f"Échec de l'authentification SerdiPay: {error_message_from_api}")
                        
            data = response.json()
            token = data.get('access_token')

            if not token:                   
                raise ValueError(f"Token d'accès non reçu de SerdiPay. Réponse complète: {data}")
            
            self._access_token = token
            return token

        except ConnectionError as e:                
            raise ConnectionError(f"Échec de connexion au serveur SerdiPay pour le token. Vérifiez votre connexion internet ou l'URL du service: {e}")
        except Timeout as e:                
            raise Timeout(f"Délai d'attente dépassé lors de la récupération du token SerdiPay. Le serveur ne répond pas à temps: {e}")
        except RequestException as e:               
            raise RequestException(f"Erreur réseau ou HTTP inattendue lors de la récupération du token SerdiPay: {e}")
        except json.JSONDecodeError:                
            raise json.JSONDecodeError("Réponse JSON invalide de SerdiPay lors de la récupération du token. La réponse du succès n'était pas du JSON valide.", doc="", pos=0)
        except ValueError as e: 
            raise ValueError(f"Erreur de données de token SerdiPay: {e}")
        except Exception as e:                  
            raise Exception(f"Une erreur système inattendue est survenue lors de la récupération du token SerdiPay: {e}")

    def recharge_account_c2b(self, client_phone, amount, currency, telecom_provider):
        """
        Effectue un rechargement C2B (Customer to Business) via SerdiPay.
        Le client paie le compte du marchand.
        Retourne un dictionnaire de succès ou d'erreur.
        """
        try:
            access_token = self._get_access_token()
        except Exception as e: # Capture toutes les exceptions possibles de _get_access_token
            return {'error': f"Impossible d'obtenir le token pour le rechargement: {e}"}

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        payload = {
            "api_id": self.API_ID,
            "api_password": self.PASSWORD, 
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
                    specific_error_message = error_data.get('message', error_data)
                except json.JSONDecodeError:
                    specific_error_message = f"Réponse d'erreur SerdiPay non JSON (Statut: {response.status_code}). Corps: '{response.text[:200]}...'"
                except Exception as e_parse:
                    specific_error_message = f"Erreur inattendue lors de l'analyse de la réponse d'erreur SerdiPay (Statut: {response.status_code}, Erreur: {e_parse})."
                
                return {'error': f"Échec du rechargement C2B: {specific_error_message}"}
            
            # En cas de succès, retourne le dictionnaire JSON de la réponse SerdiPay
            return response.json() 

        except ConnectionError as e:                
            return {'error': f"Échec de connexion au serveur SerdiPay lors du rechargement C2B. Vérifiez votre connexion internet ou l'URL du service: {e}"}
        except Timeout as e:                
            return {'error': f"Délai d'attente dépassé lors du rechargement C2B SerdiPay. Le serveur ne répond pas à temps: {e}"}
        except RequestException as e:                                   
            return {'error': f"Erreur réseau inattendue lors du rechargement C2B SerdiPay: {e}"}
        except json.JSONDecodeError:                
            return {'error': "Réponse JSON invalide lors du rechargement C2B SerdiPay. La réponse attendue pour le succès n'était pas du JSON valide."}
        except Exception as e:
            return {'error': f"Une erreur système inattendue est survenue lors du rechargement C2B: {e}"}

    def withdraw_b2c(self, client_phone, amount, currency, telecom_provider):
        """
        Effectue un retrait B2C (Business to Customer) via SerdiPay.
        Le marchand paie le client.
        Retourne un dictionnaire de succès ou d'erreur.
        """
        try:
            access_token = self._get_access_token()
        except Exception as e: # Capture toutes les exceptions possibles de _get_access_token
            return {'error': f"Impossible d'obtenir le token pour le retrait B2C: {e}"}

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        payload = {
            "clientPhone": client_phone,
            "amount": amount,
            "currency": currency,
            "telecom": telecom_provider
        }

        try:
            response = requests.post(self.B2C_URL, json=payload, headers=headers, timeout=30)

            if not response.ok:
                specific_error_message = f"Statut HTTP {response.status_code}."
                try:
                    error_data = response.json()
                    specific_error_message = error_data.get('message', error_data)
                except json.JSONDecodeError:
                    specific_error_message = f"Réponse d'erreur SerdiPay non JSON (Statut: {response.status_code}). Corps: '{response.text[:200]}...'"
                except Exception as e_parse:
                    specific_error_message = f"Erreur inattendue lors de l'analyse de la réponse d'erreur SerdiPay (Statut: {response.status_code}, Erreur: {e_parse})."
                
                return {'error': f"Échec du retrait B2C: {specific_error_message}"}

            # En cas de succès, retourne le dictionnaire JSON de la réponse SerdiPay
            return response.json()

        except ConnectionError as e:
            return {'error': f"Échec de connexion au serveur SerdiPay lors du retrait B2C. Vérifiez votre connexion internet ou l'URL du service: {e}"}
        except Timeout as e:
            return {'error': f"Délai d'attente dépassé lors du retrait B2C SerdiPay. Le serveur ne répond pas à temps: {e}"}
        except RequestException as e:
            return {'error': f"Erreur réseau inattendue lors du retrait B2C SerdiPay: {e}"}
        except json.JSONDecodeError:
            return {'error': "Réponse JSON invalide lors du retrait B2C SerdiPay. La réponse attendue pour le succès n'était pas du JSON valide."}
        except Exception as e:
            return {'error': f"Une erreur système inattendue est survenue lors du retrait B2C: {e}"}