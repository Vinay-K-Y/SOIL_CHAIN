// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title SoilNFT
 * @dev ERC-721 NFT certificate for each verified soil scan.
 *      Each scan that scores 80+ gets a unique, tamper-proof NFT.
 *      Metadata (score, farm location, timestamp) stored on IPFS.
 *
 *      This is the "proof" that judges and corporate buyers will inspect.
 */
contract SoilNFT is ERC721, ERC721URIStorage, Ownable, Pausable {

    // ── Events ────────────────────────────────────────────────────────────
    event CertificateMinted(
        uint256 indexed tokenId,
        address indexed farmer,
        string scanId,
        uint256 soilScore,
        string farmLocation
    );

    // ── State ─────────────────────────────────────────────────────────────
    uint256 private _tokenIds;

    // Metadata stored on-chain for quick lookup
    struct SoilCertificate {
        string scanId;
        address farmer;
        uint256 soilScore;      // 0-100 (stored as integer, e.g. 85 = 85.0)
        string farmLocation;
        uint256 timestamp;
        uint256 carbonTons;     // CO2 sequestered in tons
        bool isActive;          // Can be deactivated if fraud detected
    }

    mapping(uint256 => SoilCertificate) public certificates;
    mapping(string => uint256) public scanIdToTokenId; // scanId → tokenId

    // ── Constructor ───────────────────────────────────────────────────────
    constructor() ERC721("SoilCertificate", "SOILCERT") Ownable(msg.sender) {}

    // ── Minting ───────────────────────────────────────────────────────────

    /**
     * @notice Mint an NFT certificate for a verified soil scan.
     * @param farmer        Farmer's wallet address
     * @param scanId        Unique scan ID from AI backend
     * @param soilScore     Soil health score (0-100)
     * @param farmLocation  Farm location string (e.g. "Mysuru, Karnataka")
     * @param carbonTons    Estimated CO2 sequestered in tons/year
     * @param metadataURI   IPFS URI pointing to full scan metadata JSON
     */
    function mintCertificate(
        address farmer,
        string calldata scanId,
        uint256 soilScore,
        string calldata farmLocation,
        uint256 carbonTons,
        string calldata metadataURI
    ) external onlyOwner whenNotPaused returns (uint256) {
        require(farmer != address(0), "Invalid farmer address");
        require(soilScore >= 80 && soilScore <= 100, "Score must be 80+ for certificate");
        require(scanIdToTokenId[scanId] == 0, "Certificate already exists for this scan");
        require(bytes(metadataURI).length > 0, "Metadata URI required");

        _tokenIds++;
        uint256 newTokenId = _tokenIds;

        // Mint NFT to farmer
        _safeMint(farmer, newTokenId);
        _setTokenURI(newTokenId, metadataURI);

        // Store on-chain metadata
        certificates[newTokenId] = SoilCertificate({
            scanId: scanId,
            farmer: farmer,
            soilScore: soilScore,
            farmLocation: farmLocation,
            timestamp: block.timestamp,
            carbonTons: carbonTons,
            isActive: true
        });

        scanIdToTokenId[scanId] = newTokenId;

        emit CertificateMinted(newTokenId, farmer, scanId, soilScore, farmLocation);

        return newTokenId;
    }

    // ── View Functions ────────────────────────────────────────────────────

    /**
     * @notice Get full certificate details by token ID
     */
    function getCertificate(uint256 tokenId)
        external view returns (SoilCertificate memory)
    {
        require(_ownerOf(tokenId) != address(0), "Certificate does not exist");
        return certificates[tokenId];
    }

    /**
     * @notice Get token ID for a given scan ID
     */
    function getTokenIdByScan(string calldata scanId)
        external view returns (uint256)
    {
        uint256 tokenId = scanIdToTokenId[scanId];
        require(tokenId != 0, "No certificate found for this scan");
        return tokenId;
    }

    /**
     * @notice Get total certificates minted
     */
    function totalSupply() external view returns (uint256) {
        return _tokenIds;
    }

    // ── Admin ─────────────────────────────────────────────────────────────

    /**
     * @notice Deactivate a certificate if fraud is detected
     */
    function deactivateCertificate(uint256 tokenId) external onlyOwner {
        require(_ownerOf(tokenId) != address(0), "Certificate does not exist");
        certificates[tokenId].isActive = false;
    }

    function pause() external onlyOwner { _pause(); }
    function unpause() external onlyOwner { _unpause(); }

    // ── Required Overrides ────────────────────────────────────────────────
    function tokenURI(uint256 tokenId)
        public view override(ERC721, ERC721URIStorage) returns (string memory)
    {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public view override(ERC721, ERC721URIStorage) returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
