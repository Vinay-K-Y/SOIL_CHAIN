// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title SoilToken
 * @dev ERC-20 token representing verified carbon sequestration.
 *      1 SOIL token = 1 ton of CO2 captured by healthy soil.
 *
 *      Only the contract owner (SoilChain backend wallet) can mint tokens.
 *      Farmers earn tokens when their soil scan scores 80+.
 */
contract SoilToken is ERC20, Ownable, Pausable {

    // ── Events ────────────────────────────────────────────────────────────
    event TokensMinted(
        address indexed farmer,
        uint256 amount,
        string scanId,
        uint256 carbonTons
    );

    event TokensBurned(
        address indexed holder,
        uint256 amount,
        string reason
    );

    // ── State ─────────────────────────────────────────────────────────────
    uint256 public constant MAX_SUPPLY = 10_000_000 * 10**18; // 10 million tokens max

    // Track which scan IDs have already been rewarded (prevent double minting)
    mapping(string => bool) public scanRewarded;

    // Track total carbon sequestered per farmer (in tons)
    mapping(address => uint256) public farmerCarbonTons;

    // ── Constructor ───────────────────────────────────────────────────────
    constructor() ERC20("SoilToken", "SOIL") Ownable(msg.sender) {}

    // ── Minting ───────────────────────────────────────────────────────────

    /**
     * @notice Mint SoilTokens to a farmer for verified carbon sequestration.
     * @param farmer        Farmer's wallet address
     * @param carbonTons    Tons of CO2 sequestered (1 token per ton)
     * @param scanId        Unique scan ID from the AI backend (prevents double minting)
     */
    function mintForCarbon(
        address farmer,
        uint256 carbonTons,
        string calldata scanId
    ) external onlyOwner whenNotPaused {
        require(farmer != address(0), "Invalid farmer address");
        require(carbonTons > 0, "Carbon tons must be greater than 0");
        require(!scanRewarded[scanId], "This scan has already been rewarded");
        require(totalSupply() + (carbonTons * 10**18) <= MAX_SUPPLY, "Max supply exceeded");

        // Mark this scan as rewarded
        scanRewarded[scanId] = true;

        // Track farmer's contribution
        farmerCarbonTons[farmer] += carbonTons;

        // Mint 1 token per ton of CO2
        uint256 amount = carbonTons * 10**18;
        _mint(farmer, amount);

        emit TokensMinted(farmer, amount, scanId, carbonTons);
    }

    // ── Carbon Credit Purchase (burn on use) ──────────────────────────────

    /**
     * @notice Burn tokens when a corporate buyer purchases carbon credits.
     *         This "retires" the credit so it can't be double-counted.
     * @param amount    Amount of tokens to burn (in wei)
     * @param reason    Reference string (e.g. company name + year)
     */
    function retireCredits(
        uint256 amount,
        string calldata reason
    ) external whenNotPaused {
        require(amount > 0, "Amount must be greater than 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient token balance");

        _burn(msg.sender, amount);
        emit TokensBurned(msg.sender, amount, reason);
    }

    // ── View Functions ────────────────────────────────────────────────────

    /**
     * @notice Get total carbon sequestered by a farmer in tons
     */
    function getCarbonContribution(address farmer) external view returns (uint256) {
        return farmerCarbonTons[farmer];
    }

    /**
     * @notice Check if a scan has already been rewarded
     */
    function isScanRewarded(string calldata scanId) external view returns (bool) {
        return scanRewarded[scanId];
    }

    // ── Admin ─────────────────────────────────────────────────────────────

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }
}
