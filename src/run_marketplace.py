from marketplace_images import SellerAsset, client_from_environment, prepare_listing
import struct
import zlib


def sample_png() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    pixels = b"".join(b"\x00" + b"\x65\x91\x73" * 64 for _ in range(64))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 64, 64, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(pixels))
            + chunk(b"IEND", b""))


def main() -> None:
    client = client_from_environment()
    update, handoff = prepare_listing(SellerAsset("lamp.png", sample_png()), "listing-1042", client)
    print(update)
    print(handoff)


if __name__ == "__main__":
    main()
