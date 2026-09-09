package ar.gov.justiciajujuy.sanpedro.inventario.security;

import java.math.BigInteger;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.List;

public class NetworkAddressPolicy {

	private final List<CidrBlock> allowedNetworks;

	public NetworkAddressPolicy(List<String> allowedCidrs) {
		this.allowedNetworks = allowedCidrs.stream()
				.map(CidrBlock::parse)
				.toList();
	}

	public boolean isAllowed(String address) {
		try {
			InetAddress inetAddress = InetAddress.getByName(address);
			if (inetAddress.isAnyLocalAddress() || inetAddress.isLoopbackAddress()) {
				return true;
			}
			return allowedNetworks.stream().anyMatch(network -> network.contains(inetAddress));
		} catch (UnknownHostException ex) {
			return false;
		}
	}

	public boolean isLoopback(String address) {
		try {
			return InetAddress.getByName(address).isLoopbackAddress();
		} catch (UnknownHostException ex) {
			return false;
		}
	}

	private record CidrBlock(BigInteger network, BigInteger mask, int bytes) {

		private static CidrBlock parse(String cidr) {
			try {
				String[] parts = cidr.split("/", 2);
				InetAddress address = InetAddress.getByName(parts[0]);
				byte[] rawAddress = address.getAddress();
				int totalBits = rawAddress.length * 8;
				int prefixLength = parts.length == 2 ? Integer.parseInt(parts[1]) : totalBits;
				if (prefixLength < 0 || prefixLength > totalBits) {
					throw new IllegalArgumentException("Prefijo CIDR invalido: " + cidr);
				}
				BigInteger allBits = BigInteger.ONE.shiftLeft(totalBits).subtract(BigInteger.ONE);
				BigInteger mask = prefixLength == 0
						? BigInteger.ZERO
						: allBits.shiftRight(totalBits - prefixLength).shiftLeft(totalBits - prefixLength);
				BigInteger network = new BigInteger(1, rawAddress).and(mask);
				return new CidrBlock(network, mask, rawAddress.length);
			} catch (Exception ex) {
				throw new IllegalArgumentException("Red permitida invalida: " + cidr, ex);
			}
		}

		private boolean contains(InetAddress address) {
			byte[] rawAddress = address.getAddress();
			if (rawAddress.length != bytes) {
				return false;
			}
			return new BigInteger(1, rawAddress).and(mask).equals(network);
		}
	}
}
