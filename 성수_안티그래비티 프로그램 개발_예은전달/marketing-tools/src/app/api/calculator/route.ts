import { prisma } from "@/lib/db";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const period = searchParams.get("period");

  const where = period ? { period } : {};
  const records = await prisma.settlementRecord.findMany({
    where,
    orderBy: { createdAt: "desc" },
  });

  return NextResponse.json(records);
}

export async function POST(request: Request) {
  const body = await request.json();

  const {
    period,
    serviceName,
    serviceType = "general",
    grossRevenue,
    commissionRate,
    rentalCost = 0,
    internetCost = 0,
    otherExpenses = 0,
    notes,
  } = body;

  const commissionAmount = grossRevenue * commissionRate;
  const netProfit =
    grossRevenue - commissionAmount - rentalCost - internetCost - otherExpenses;

  const record = await prisma.settlementRecord.create({
    data: {
      period,
      serviceName,
      serviceType,
      grossRevenue,
      commissionRate,
      commissionAmount,
      rentalCost,
      internetCost,
      otherExpenses,
      netProfit,
      notes,
    },
  });

  return NextResponse.json(record);
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const id = searchParams.get("id");

  if (!id) {
    return NextResponse.json({ error: "ID required" }, { status: 400 });
  }

  await prisma.settlementRecord.delete({ where: { id } });
  return NextResponse.json({ success: true });
}
