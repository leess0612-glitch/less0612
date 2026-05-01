-- CreateTable
CREATE TABLE "SettlementRecord" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "period" TEXT NOT NULL,
    "serviceName" TEXT NOT NULL,
    "serviceType" TEXT NOT NULL DEFAULT 'general',
    "grossRevenue" REAL NOT NULL,
    "commissionRate" REAL NOT NULL,
    "commissionAmount" REAL NOT NULL,
    "rentalCost" REAL NOT NULL DEFAULT 0,
    "internetCost" REAL NOT NULL DEFAULT 0,
    "otherExpenses" REAL NOT NULL DEFAULT 0,
    "netProfit" REAL NOT NULL,
    "notes" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "ScriptAnalysis" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "sourceType" TEXT NOT NULL,
    "sourceContent" TEXT NOT NULL,
    "result" TEXT NOT NULL,
    "generatedScript" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "LandingPageProject" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "sourceUrl" TEXT,
    "analysisResult" TEXT,
    "generatedHtml" TEXT,
    "screenshotUrl" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "ReelsProject" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "title" TEXT NOT NULL,
    "script" TEXT NOT NULL,
    "platform" TEXT NOT NULL,
    "videoUrl" TEXT,
    "uploadId" TEXT,
    "status" TEXT NOT NULL DEFAULT 'draft',
    "metrics" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);
