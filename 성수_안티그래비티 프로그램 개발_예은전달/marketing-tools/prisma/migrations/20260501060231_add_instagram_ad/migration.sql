-- CreateTable
CREATE TABLE "InstagramAd" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "serviceType" TEXT NOT NULL,
    "productName" TEXT NOT NULL,
    "price" TEXT,
    "features" TEXT NOT NULL,
    "adCopy" TEXT,
    "imageUrl" TEXT,
    "imagePrompt" TEXT,
    "caption" TEXT,
    "hashtags" TEXT,
    "status" TEXT NOT NULL DEFAULT 'draft',
    "instagramId" TEXT,
    "postedAt" DATETIME,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);
