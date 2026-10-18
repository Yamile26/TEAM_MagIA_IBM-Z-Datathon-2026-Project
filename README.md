# Team MagIA Datathon 2026 Project: Pasaporte Cuántico

**Tema 2: AI Secured, Innovation Without Exposure.**
Inventaría el cifrado vulnerable de una institución, prioriza qué migrar según cuánto tiempo deben seguir secretos sus datos, migra un servicio a TLS híbrido post-cuántico y emite un pasaporte firmado con ML-DSA. Todo corre en IBM LinuxONE (s390x).

## Flujo
escáner -> inventario CBOM (CycloneDX) -> ranking (Mosca + XGBoost) -> plan + validador -> TLS híbrido -> pasaporte firmado

## Cómo correrlo
```bash
python3 scanner/scan.py lab/hospital_demo   # hallazgos
python3 cbom/make_cbom.py                   # CBOM CycloneDX
python3 risk/mosca.py                       # ranking por reglas (desigualdad de Mosca)
python3 ml/train_risk.py                    # ranking con XGBoost
python3 ml/detector.py                      # detector ML de uso criptográfico
python3 planner/plan.py                     # plan + validador TLS
bash passport/sign.sh                       # pasaporte firmado ML-DSA-65
python3 dashboard/app.py                    # panel (o en contenedor: dashboard/Containerfile)
```

## Resultados medidos (IBM LinuxONE, s390x, OpenSSL 3.5.0 compilado en la instancia)
* Handshake TLS 1.3, 50 intentos, 50/50 exitosos en ambos: X25519 6.4 ms, X25519MLKEM768 6.5 ms por intento. Incluye el arranque del proceso `openssl`; sirve para comparar, no es latencia pura.
* Firma, 100 repeticiones (también incluye arranque del proceso): ECDSA P-256 3.3 ms, ML-DSA-65 5.0 ms.
* `openssl speed`: ECDSA P-256 ~64,000 firmas/s; RSA-2048 ~540 firmas/s.
* Verificación: pasaporte original válido; con un carácter alterado, la firma se rechaza.
* Detector ML en banco sintético con sintaxis no vista: solo regex precisión 1.00 / recall 0.54; regex + ML precisión 0.62 / recall 0.85.

## Limitaciones (transparencia)
* El modelo XGBoost se entrena con **etiquetas de reglas expertas** sobre un inventario sintético de 2,000 activos. Su correlación alta mide cuánto copia las reglas, no riesgo real. Siguiente paso: calibrar con instituciones reales.
* El banco del detector ML es sintético y las variantes de prueba las escribió el equipo. El ML sube el recall a costa de precisión y marca falsos positivos (por ejemplo `import hashlib`): se propone como segundo filtro con revisión humana.
* El planificador usa **plantillas más un validador real**. No se usó un LLM.
* Z (años hasta una amenaza cuántica relevante) es un supuesto configurable, no una predicción. Los años de vida del dato y de migración también son supuestos declarados.
* Los niveles del pasaporte son criterios del equipo, no un estándar ni una certificación legal ni de cumplimiento.
* PyTorch no tiene paquetes para s390x en PyPI, por eso no se usó. Frameworks de IA usados: XGBoost y scikit-learn.
* No se afirma uso de aceleradores de hardware de IA (Telum) ni de otras capacidades que no se hayan comprobado.

## Equipo
| Integrante | Contribución |
|---|---|
| (completar) | (completar) |

## Librerías y estándares de código abierto
* [OpenSSL 3.5](https://www.openssl.org/) (ML-KEM, ML-DSA, TLS híbrido)
* [XGBoost](https://xgboost.readthedocs.io/) · [scikit-learn](https://scikit-learn.org/) · [pandas](https://pandas.pydata.org/) · [NumPy](https://numpy.org/) · [SciPy](https://scipy.org/)
* [Flask](https://flask.palletsprojects.com/) · [Podman](https://podman.io/)
* [CycloneDX CBOM](https://cyclonedx.org/capabilities/cbom/)
* NIST FIPS 203 (ML-KEM) y FIPS 204 (ML-DSA)

Código escrito durante el hackathon. El Hospital Regional Demo es ficticio.

## Experimento: Granite con y sin ejemplos
Mismo modelo (Granite 4.0 H 350M base), 3 activos x 10 repeticiones x 3 candidatos. Con 2 ejemplos en el prompt: 29/30 válidas al primer intento y 30/30 con validación. Sin ejemplos: 0/30, y las 30 pruebas cayeron a la plantilla. Las respuestas sin ejemplos no eran nombres de grupo (el modelo contestó versiones de TLS y tamaños de clave), así que las frenó el filtro de formato antes de llegar a la prueba TLS; la prueba TLS real (handshake) es la segunda capa y rechazó un grupo inexistente en la demo de plan.py. Muestra pequeña y un solo modelo: no es una comparación general de LLMs.

## Librerías y modelos adicionales
- [llama.cpp](https://github.com/ggml-org/llama.cpp) y [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) (ejecución local de Granite)
- [IBM Granite](https://huggingface.co/ibm-granite) (modelo 4.0 H 350M base)
- [PyTorch](https://github.com/pytorch/pytorch) (versión CPU) y [Docker](https://github.com/moby/moby)
- Datos: ninguno externo, todo sintético y generado durante el evento
