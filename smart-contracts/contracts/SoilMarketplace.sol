// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./SoilToken.sol";

/**
 * @title SoilMarketplace
 * @dev Handles two marketplace actions:
 *      1. Microbiome Rentals — farmers rent healthy soil bacteria to others
 *      2. Carbon Credit Trading — corporates buy SoilTokens from farmers
 *
 *      Smart contracts ensure payments are automatic, trustless, and transparent.
 *      No broker needed — farmers get paid directly.
 */
contract SoilMarketplace is Ownable, Pausable, ReentrancyGuard {

    SoilToken public soilToken;

    // ── Platform Fee ──────────────────────────────────────────────────────
    // SoilChain takes 10% platform fee, farmer gets 90%
    // (vs 40-60% with traditional carbon brokers)
    uint256 public platformFeePercent = 10;
    address public feeRecipient;

    // ── Microbiome Rental ─────────────────────────────────────────────────
    struct MicrobiomeListing {
        uint256 listingId;
        address payable farmer;
        string farmLocation;
        uint256 soilScore;          // Verified score from AI (must be 80+)
        uint256 pricePerMonthWei;   // Price in MATIC (wei)
        uint256 availableKg;
        bool isActive;
        uint256 createdAt;
    }

    struct RentalAgreement {
        uint256 rentalId;
        uint256 listingId;
        address payable renter;
        address payable farmer;
        uint256 durationMonths;
        uint256 totalPaidWei;
        uint256 startTime;
        bool isCompleted;
        bool paymentReleased;
    }

    uint256 private _listingIds;
    uint256 private _rentalIds;

    mapping(uint256 => MicrobiomeListing) public listings;
    mapping(uint256 => RentalAgreement) public rentals;
    mapping(address => uint256[]) public farmerListings;
    mapping(address => uint256[]) public renterAgreements;

    // ── Carbon Credit Trading ─────────────────────────────────────────────
    struct CreditOffer {
        uint256 offerId;
        address payable farmer;
        uint256 tokenAmount;        // SOIL tokens being sold
        uint256 pricePerTokenWei;   // Price per token in MATIC
        bool isActive;
        uint256 createdAt;
    }

    uint256 private _offerIds;
    mapping(uint256 => CreditOffer) public creditOffers;

    // ── Events ────────────────────────────────────────────────────────────
    event ListingCreated(uint256 indexed listingId, address indexed farmer, uint256 soilScore, uint256 pricePerMonth);
    event RentalCreated(uint256 indexed rentalId, uint256 indexed listingId, address indexed renter, uint256 durationMonths);
    event RentalCompleted(uint256 indexed rentalId, address indexed farmer, uint256 amountReleased);
    event CreditOfferCreated(uint256 indexed offerId, address indexed farmer, uint256 tokenAmount, uint256 pricePerToken);
    event CreditsPurchased(uint256 indexed offerId, address indexed buyer, uint256 tokenAmount, uint256 totalPaid);

    // ── Constructor ───────────────────────────────────────────────────────
    constructor(address soilTokenAddress) Ownable(msg.sender) {
        soilToken = SoilToken(soilTokenAddress);
        feeRecipient = msg.sender;
    }

    // ════════════════════════════════════════════════════════════════════
    // MICROBIOME RENTAL MARKETPLACE
    // ════════════════════════════════════════════════════════════════════

    /**
     * @notice Farmer lists their healthy microbiome for rent.
     *         Only farms with soil score 80+ can list.
     * @param soilScore         Verified soil score from AI backend
     * @param farmLocation      Location string
     * @param pricePerMonthWei  Monthly rental price in MATIC (wei)
     * @param availableKg       Kg of microbiome available
     */
    function createListing(
        uint256 soilScore,
        string calldata farmLocation,
        uint256 pricePerMonthWei,
        uint256 availableKg
    ) external whenNotPaused returns (uint256) {
        require(soilScore >= 80, "Soil score must be 80+ to list microbiomes");
        require(pricePerMonthWei > 0, "Price must be greater than 0");
        require(availableKg > 0, "Must have available quantity");

        _listingIds++;
        uint256 listingId = _listingIds;

        listings[listingId] = MicrobiomeListing({
            listingId: listingId,
            farmer: payable(msg.sender),
            farmLocation: farmLocation,
            soilScore: soilScore,
            pricePerMonthWei: pricePerMonthWei,
            availableKg: availableKg,
            isActive: true,
            createdAt: block.timestamp
        });

        farmerListings[msg.sender].push(listingId);

        emit ListingCreated(listingId, msg.sender, soilScore, pricePerMonthWei);
        return listingId;
    }

    /**
     * @notice Renter pays upfront for microbiome rental.
     *         Payment is held in escrow until rental period ends.
     * @param listingId         The listing to rent from
     * @param durationMonths    How many months to rent
     */
    function rentMicrobiome(
        uint256 listingId,
        uint256 durationMonths
    ) external payable nonReentrant whenNotPaused returns (uint256) {
        MicrobiomeListing storage listing = listings[listingId];
        require(listing.isActive, "Listing is not active");
        require(listing.farmer != msg.sender, "Cannot rent your own listing");
        require(durationMonths >= 1 && durationMonths <= 12, "Duration must be 1-12 months");

        uint256 totalCost = listing.pricePerMonthWei * durationMonths;
        require(msg.value >= totalCost, "Insufficient payment sent");

        _rentalIds++;
        uint256 rentalId = _rentalIds;

        rentals[rentalId] = RentalAgreement({
            rentalId: rentalId,
            listingId: listingId,
            renter: payable(msg.sender),
            farmer: listing.farmer,
            durationMonths: durationMonths,
            totalPaidWei: msg.value,
            startTime: block.timestamp,
            isCompleted: false,
            paymentReleased: false
        });

        renterAgreements[msg.sender].push(rentalId);

        // Refund excess payment
        if (msg.value > totalCost) {
            payable(msg.sender).transfer(msg.value - totalCost);
        }

        emit RentalCreated(rentalId, listingId, msg.sender, durationMonths);
        return rentalId;
    }

    /**
     * @notice Release payment to farmer after rental period ends.
     *         Platform fee deducted automatically.
     * @param rentalId  The rental agreement to complete
     */
    function completeRental(uint256 rentalId) external nonReentrant {
        RentalAgreement storage rental = rentals[rentalId];
        require(!rental.isCompleted, "Rental already completed");
        require(!rental.paymentReleased, "Payment already released");

        uint256 rentalEndTime = rental.startTime + (rental.durationMonths * 30 days);
        require(
            block.timestamp >= rentalEndTime || msg.sender == owner(),
            "Rental period not yet complete"
        );

        rental.isCompleted = true;
        rental.paymentReleased = true;

        // Calculate platform fee (10%) and farmer payment (90%)
        uint256 platformFee = (rental.totalPaidWei * platformFeePercent) / 100;
        uint256 farmerPayment = rental.totalPaidWei - platformFee;

        // Transfer payments
        payable(feeRecipient).transfer(platformFee);
        rental.farmer.transfer(farmerPayment);

        emit RentalCompleted(rentalId, rental.farmer, farmerPayment);
    }

    // ════════════════════════════════════════════════════════════════════
    // CARBON CREDIT TRADING
    // ════════════════════════════════════════════════════════════════════

    /**
     * @notice Farmer lists SoilTokens for sale as carbon credits.
     * @param tokenAmount       Number of SOIL tokens to sell (in wei)
     * @param pricePerTokenWei  Price per token in MATIC (wei)
     */
    function createCreditOffer(
        uint256 tokenAmount,
        uint256 pricePerTokenWei
    ) external whenNotPaused returns (uint256) {
        require(tokenAmount > 0, "Token amount must be greater than 0");
        require(pricePerTokenWei > 0, "Price must be greater than 0");
        require(
            soilToken.balanceOf(msg.sender) >= tokenAmount,
            "Insufficient SoilToken balance"
        );

        // Transfer tokens to marketplace escrow
        soilToken.transferFrom(msg.sender, address(this), tokenAmount);

        _offerIds++;
        uint256 offerId = _offerIds;

        creditOffers[offerId] = CreditOffer({
            offerId: offerId,
            farmer: payable(msg.sender),
            tokenAmount: tokenAmount,
            pricePerTokenWei: pricePerTokenWei,
            isActive: true,
            createdAt: block.timestamp
        });

        emit CreditOfferCreated(offerId, msg.sender, tokenAmount, pricePerTokenWei);
        return offerId;
    }

    /**
     * @notice Corporate buyer purchases carbon credits from a farmer.
     *         Tokens transferred to buyer, MATIC sent to farmer.
     * @param offerId   The credit offer to purchase
     */
    function purchaseCredits(uint256 offerId)
        external payable nonReentrant whenNotPaused
    {
        CreditOffer storage offer = creditOffers[offerId];
        require(offer.isActive, "Offer is not active");
        require(offer.farmer != msg.sender, "Cannot buy your own credits");

        uint256 totalCost = (offer.tokenAmount * offer.pricePerTokenWei) / 10**18;
        require(msg.value >= totalCost, "Insufficient payment");

        offer.isActive = false;

        // Platform fee
        uint256 platformFee = (msg.value * platformFeePercent) / 100;
        uint256 farmerPayment = msg.value - platformFee;

        // Send MATIC to farmer and fee to platform
        offer.farmer.transfer(farmerPayment);
        payable(feeRecipient).transfer(platformFee);

        // Transfer SOIL tokens to buyer
        soilToken.transfer(msg.sender, offer.tokenAmount);

        // Refund excess
        if (msg.value > totalCost) {
            payable(msg.sender).transfer(msg.value - totalCost);
        }

        emit CreditsPurchased(offerId, msg.sender, offer.tokenAmount, msg.value);
    }

    // ── View Functions ────────────────────────────────────────────────────

    function getListing(uint256 listingId) external view returns (MicrobiomeListing memory) {
        return listings[listingId];
    }

    function getRental(uint256 rentalId) external view returns (RentalAgreement memory) {
        return rentals[rentalId];
    }

    function getCreditOffer(uint256 offerId) external view returns (CreditOffer memory) {
        return creditOffers[offerId];
    }

    function getFarmerListings(address farmer) external view returns (uint256[] memory) {
        return farmerListings[farmer];
    }

    function getRenterAgreements(address renter) external view returns (uint256[] memory) {
        return renterAgreements[renter];
    }

    function getTotalListings() external view returns (uint256) { return _listingIds; }
    function getTotalRentals() external view returns (uint256) { return _rentalIds; }
    function getTotalOffers() external view returns (uint256) { return _offerIds; }

    // ── Admin ─────────────────────────────────────────────────────────────

    function updatePlatformFee(uint256 newFeePercent) external onlyOwner {
        require(newFeePercent <= 20, "Fee cannot exceed 20%");
        platformFeePercent = newFeePercent;
    }

    function updateFeeRecipient(address newRecipient) external onlyOwner {
        require(newRecipient != address(0), "Invalid address");
        feeRecipient = newRecipient;
    }

    function pause() external onlyOwner { _pause(); }
    function unpause() external onlyOwner { _unpause(); }
}
