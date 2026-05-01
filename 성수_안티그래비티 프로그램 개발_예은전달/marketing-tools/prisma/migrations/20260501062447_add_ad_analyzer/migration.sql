-- CreateTable
CREATE TABLE "AdAnalysis" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "sourceUrl" TEXT NOT NULL,
    "platform" TEXT NOT NULL,
    "title" TEXT,
    "transcript" TEXT,
    "adStructure" TEXT,
    "scriptStyle" TEXT,
    "visualStyle" TEXT,
    "hooks" TEXT,
    "targetAudience" TEXT,
    "rawAnalysis" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "GeneratedAd" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "analysisId" TEXT NOT NULL,
    "adType" TEXT NOT NULL,
    "productName" TEXT NOT NULL,
    "serviceType" TEXT NOT NULL,
    "videoPath" TEXT,
    "script" TEXT,
    "caption" TEXT,
    "hashtags" TEXT,
    "status" TEXT NOT NULL DEFAULT 'generated',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "GeneratedAd_analysisId_fkey" FOREIGN KEY ("analysisId") REFERENCES "AdAnalysis" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "AdUpload" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "generatedAdId" TEXT NOT NULL,
    "platform" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "platformId" TEXT,
    "error" TEXT,
    "uploadedAt" DATETIME,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "AdUpload_generatedAdId_fkey" FOREIGN KEY ("generatedAdId") REFERENCES "GeneratedAd" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);
