const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("═══════════════════════════════════════════");
  console.log("  SoilChain Smart Contract Deployment");
  console.log("═══════════════════════════════════════════");
  console.log(`  Deployer: ${deployer.address}`);
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log(`  Balance:  ${ethers.formatEther(balance)} MATIC\n`);

  // 1. Deploy SoilToken (ERC-20)
  console.log("1️⃣  Deploying SoilToken (ERC-20)...");
  const SoilToken = await ethers.getContractFactory("SoilToken");
  const soilToken = await SoilToken.deploy();
  await soilToken.waitForDeployment();
  const soilTokenAddr = await soilToken.getAddress();
  console.log(`   ✅ SoilToken deployed: ${soilTokenAddr}`);

  // 2. Deploy SoilNFT (ERC-721)
  console.log("\n2️⃣  Deploying SoilNFT (ERC-721)...");
  const SoilNFT = await ethers.getContractFactory("SoilNFT");
  const soilNFT = await SoilNFT.deploy();
  await soilNFT.waitForDeployment();
  const soilNFTAddr = await soilNFT.getAddress();
  console.log(`   ✅ SoilNFT deployed: ${soilNFTAddr}`);

  // 3. Deploy SoilMarketplace
  console.log("\n3️⃣  Deploying SoilMarketplace...");
  const SoilMarketplace = await ethers.getContractFactory("SoilMarketplace");
  const marketplace = await SoilMarketplace.deploy(soilTokenAddr);
  await marketplace.waitForDeployment();
  const marketplaceAddr = await marketplace.getAddress();
  console.log(`   ✅ SoilMarketplace deployed: ${marketplaceAddr}`);

  // Save addresses to deployment.json
  const deployment = {
    network:          "Polygon Amoy Testnet",
    chainId:          80002,
    deployer:         deployer.address,
    deployedAt:       new Date().toISOString(),
    contracts: {
      SoilToken:       soilTokenAddr,
      SoilNFT:         soilNFTAddr,
      SoilMarketplace: marketplaceAddr,
    },
    explorerUrls: {
      SoilToken:       `https://amoy.polygonscan.com/address/${soilTokenAddr}`,
      SoilNFT:         `https://amoy.polygonscan.com/address/${soilNFTAddr}`,
      SoilMarketplace: `https://amoy.polygonscan.com/address/${marketplaceAddr}`,
    }
  };

  fs.writeFileSync("deployment.json", JSON.stringify(deployment, null, 2));

  console.log("\n═══════════════════════════════════════════");
  console.log("  ✅ ALL CONTRACTS DEPLOYED SUCCESSFULLY!");
  console.log("═══════════════════════════════════════════");
  console.log(`\n  SoilToken:       ${soilTokenAddr}`);
  console.log(`  SoilNFT:         ${soilNFTAddr}`);
  console.log(`  SoilMarketplace: ${marketplaceAddr}`);
  console.log(`\n  🔗 View on PolygonScan:`);
  console.log(`  ${deployment.explorerUrls.SoilToken}`);
  console.log(`  ${deployment.explorerUrls.SoilNFT}`);
  console.log(`  ${deployment.explorerUrls.SoilMarketplace}`);
  console.log(`\n  📄 Addresses saved to: deployment.json`);
  console.log("═══════════════════════════════════════════\n");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
