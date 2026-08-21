import argparse
import datetime
import ipaddress
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def _write_private_key(path, key):
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


def _ip_san(value):
    return x509.IPAddress(ipaddress.ip_address(value))


def main():
    parser = argparse.ArgumentParser(description="Genera CA local y certificado HTTPS para Inventario.")
    parser.add_argument(
        "--ip",
        action="append",
        required=True,
        help="IP que debe cubrir el certificado. Se puede repetir: --ip 192.168.1.8 --ip 10.15.2.251",
    )
    parser.add_argument("--days", type=int, default=825, help="Vigencia del certificado en dias.")
    args = parser.parse_args()

    ips = []
    for value in args.ip:
        ipaddress.ip_address(value)
        if value not in ips:
            ips.append(value)

    now = datetime.datetime.now(datetime.timezone.utc)
    root_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    root_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Inventario GOLD Local"),
            x509.NameAttribute(NameOID.COMMON_NAME, "Inventario GOLD Local Root CA"),
        ]
    )
    root_cert = (
        x509.CertificateBuilder()
        .subject_name(root_subject)
        .issuer_name(root_subject)
        .public_key(root_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=args.days))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(root_key.public_key()), critical=False)
        .sign(root_key, hashes.SHA256())
    )

    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Inventario GOLD Local"),
            x509.NameAttribute(NameOID.COMMON_NAME, ips[0]),
        ]
    )
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(server_subject)
        .issuer_name(root_cert.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=5))
        .not_valid_after(now + datetime.timedelta(days=args.days))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectAlternativeName([_ip_san(ip) for ip in ips]), critical=False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(server_key.public_key()), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(root_key.public_key()), critical=False)
        .sign(root_key, hashes.SHA256())
    )

    Path("inventario-local-ca.key").write_bytes(
        root_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    Path("inventario-local-ca.crt").write_bytes(root_cert.public_bytes(serialization.Encoding.PEM))
    Path("inventario-cert.crt").write_bytes(root_cert.public_bytes(serialization.Encoding.PEM))
    Path("cert.pem").write_bytes(server_cert.public_bytes(serialization.Encoding.PEM))
    _write_private_key(Path("key.pem"), server_key)

    print("Certificados generados.")
    print("Servidor: cert.pem / key.pem")
    print("CA para instalar en celulares/PCs: inventario-local-ca.crt")
    print("IPs incluidas: " + ", ".join(ips))


if __name__ == "__main__":
    main()
