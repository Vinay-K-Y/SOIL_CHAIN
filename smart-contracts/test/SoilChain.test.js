/**
 * SoilChain Contract Tests
 * =========================
 * End-to-end tests for all 3 contracts.
 * Run: npx hardhat test
 */

const { expect } = require("chai");
const { ethers }  = require("hardhat");

describe("🌱 SoilChain Smart Contracts", function () {

  let soilToken, soilNFT, marketplace;
  let owner, farmer1, farmer2, corporate;

  beforeEach(async function () {
    [owner, farmer1, farmer2, corporate] = await ethers.getSigners();
    soilToken   = await ethers.deployContract("SoilToken");
    soilNFT     = await ethers.deployContract("SoilNFT");
    marketplace = await ethers.deployContract("SoilMarketplace", [
      await soilToken.getAddress()
    ]);
  });

  // ── SoilToken (ERC-20) ────────────────────────────────────────────────
  describe("🪙  SoilToken (ERC-20 Carbon Credit)", function () {

    it("Has correct name and symbol", async function () {
      expect(await soilToken.name()).to.equal("SoilToken");
      expect(await soilToken.symbol()).to.equal("SOIL");
    });

    it("Mints tokens for verified soil scan", async function () {
      await soilToken.mintForCarbon(farmer1.address, 4, "scan_mysuru_001");
      const balance = await soilToken.balanceOf(farmer1.address);
      expect(balance).to.equal(ethers.parseEther("4"));
    });

    it("Blocks double-minting for same scan ID", async function () {
      await soilToken.mintForCarbon(farmer1.address, 4, "scan_pune_001");
      await expect(
        soilToken.mintForCarbon(farmer1.address, 4, "scan_pune_001")
      ).to.be.revertedWith("This scan has already been rewarded");
    });

    it("Tracks cumulative farmer carbon contribution", async function () {
      await soilToken.mintForCarbon(farmer1.address, 4, "scan_001");
      await soilToken.mintForCarbon(farmer1.address, 6, "scan_002");
      const contribution = await soilToken.getCarbonContribution(farmer1.address);
      expect(contribution).to.equal(10); // 4 + 6 = 10 tons
    });

    it("Only owner can mint (access control)", async function () {
      await expect(
        soilToken.connect(farmer1).mintForCarbon(farmer2.address, 4, "scan_hack")
      ).to.be.reverted;
    });

    it("Farmer can retire (burn) credits for ESG compliance", async function () {
      await soilToken.mintForCarbon(farmer1.address, 10, "scan_retire_001");
      const burnAmount = ethers.parseEther("5");
      await soilToken.connect(farmer1).retireCredits(burnAmount, "Infosys Net Zero 2025");
      const balance = await soilToken.balanceOf(farmer1.address);
      expect(balance).to.equal(ethers.parseEther("5")); // 10 - 5 = 5 left
    });
  });

  // ── SoilNFT (ERC-721) ────────────────────────────────────────────────
  describe("🏆  SoilNFT (ERC-721 Certificate)", function () {

    it("Mints NFT certificate for 80+ score scan", async function () {
      await soilNFT.mintCertificate(
        farmer1.address, "scan_nft_001", 85,
        "Mysuru, Karnataka", 4,
        "ipfs://QmSoilChain/scan_nft_001"
      );
      expect(await soilNFT.ownerOf(1)).to.equal(farmer1.address);
      expect(await soilNFT.totalSupply()).to.equal(1);
    });

    it("Rejects certificate for score below 80", async function () {
      await expect(
        soilNFT.mintCertificate(
          farmer1.address, "scan_low", 75,
          "Pune", 2, "ipfs://QmSoilChain/low"
        )
      ).to.be.revertedWith("Score must be 80+ for certificate");
    });

    it("Stores correct metadata on-chain", async function () {
      await soilNFT.mintCertificate(
        farmer1.address, "scan_meta_001", 92,
        "Nashik, Maharashtra", 5,
        "ipfs://QmSoilChain/scan_meta_001"
      );
      const cert = await soilNFT.getCertificate(1);
      expect(cert.soilScore).to.equal(92);
      expect(cert.farmLocation).to.equal("Nashik, Maharashtra");
      expect(cert.carbonTons).to.equal(5);
      expect(cert.isActive).to.equal(true);
    });

    it("Blocks duplicate certificate for same scan", async function () {
      await soilNFT.mintCertificate(
        farmer1.address, "scan_dup", 88, "Mysuru", 4, "ipfs://test"
      );
      await expect(
        soilNFT.mintCertificate(
          farmer1.address, "scan_dup", 88, "Mysuru", 4, "ipfs://test"
        )
      ).to.be.revertedWith("Certificate already exists for this scan");
    });
  });

  // ── SoilMarketplace ──────────────────────────────────────────────────
  describe("🏪  SoilMarketplace (Microbiome + Carbon)", function () {

    const pricePerMonth = ethers.parseEther("0.1"); // 0.1 MATIC/month

    it("Farmer with 80+ score can create microbiome listing", async function () {
      await marketplace.connect(farmer1).createListing(
        85, "Mysuru, Karnataka", pricePerMonth, 50
      );
      const listing = await marketplace.getListing(1);
      expect(listing.farmer).to.equal(farmer1.address);
      expect(listing.soilScore).to.equal(85);
      expect(listing.isActive).to.equal(true);
    });

    it("Rejects listing for score below 80", async function () {
      await expect(
        marketplace.connect(farmer1).createListing(70, "Mysuru", pricePerMonth, 50)
      ).to.be.revertedWith("Soil score must be 80+ to list microbiomes");
    });

    it("Renter pays and rental agreement is created", async function () {
      await marketplace.connect(farmer1).createListing(85, "Mysuru", pricePerMonth, 50);
      const totalCost = pricePerMonth * BigInt(3);
      await marketplace.connect(farmer2).rentMicrobiome(1, 3, { value: totalCost });
      const rental = await marketplace.getRental(1);
      expect(rental.renter).to.equal(farmer2.address);
      expect(rental.durationMonths).to.equal(3);
      expect(rental.isCompleted).to.equal(false);
    });

    it("Farmer can list and corporate can purchase carbon credits", async function () {
      // Mint 10 tokens for farmer1
      await soilToken.mintForCarbon(farmer1.address, 10, "scan_market_001");
      const tokenAmount  = ethers.parseEther("5");
      const pricePerToken = ethers.parseEther("0.01");

      // Approve marketplace to move tokens
      await soilToken.connect(farmer1).approve(
        await marketplace.getAddress(), tokenAmount
      );

      // Create carbon credit offer
      await marketplace.connect(farmer1).createCreditOffer(tokenAmount, pricePerToken);

      // Corporate purchases credits
      const totalCost = (tokenAmount * pricePerToken) / ethers.parseEther("1");
      await marketplace.connect(corporate).purchaseCredits(1, { value: totalCost });

      // Corporate now holds the tokens
      const balance = await soilToken.balanceOf(corporate.address);
      expect(balance).to.equal(tokenAmount);
    });
  });
});
