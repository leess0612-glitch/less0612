"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { Trash2, Plus } from "lucide-react";

interface SettlementRecord {
  id: string;
  period: string;
  serviceName: string;
  serviceType: string;
  grossRevenue: number;
  commissionRate: number;
  commissionAmount: number;
  rentalCost: number;
  internetCost: number;
  otherExpenses: number;
  netProfit: number;
  notes: string | null;
  createdAt: string;
}

const currentMonth = new Date().toISOString().slice(0, 7);

export default function CalculatorPage() {
  const [records, setRecords] = useState<SettlementRecord[]>([]);
  const [filterPeriod, setFilterPeriod] = useState("");
  const [loading, setLoading] = useState(false);

  // Form state
  const [period, setPeriod] = useState(currentMonth);
  const [serviceName, setServiceName] = useState("");
  const [serviceType, setServiceType] = useState("general");
  const [grossRevenue, setGrossRevenue] = useState("");
  const [commissionRate, setCommissionRate] = useState("");
  const [rentalCost, setRentalCost] = useState("");
  const [internetCost, setInternetCost] = useState("");
  const [otherExpenses, setOtherExpenses] = useState("");
  const [notes, setNotes] = useState("");

  // Calculated preview
  const revenue = parseFloat(grossRevenue) || 0;
  const rate = parseFloat(commissionRate) / 100 || 0;
  const rental = parseFloat(rentalCost) || 0;
  const internet = parseFloat(internetCost) || 0;
  const other = parseFloat(otherExpenses) || 0;
  const commissionAmount = revenue * rate;
  const netProfit = revenue - commissionAmount - rental - internet - other;

  const fetchRecords = useCallback(async () => {
    const params = filterPeriod ? `?period=${filterPeriod}` : "";
    const res = await fetch(`/api/calculator${params}`);
    const data = await res.json();
    setRecords(data);
  }, [filterPeriod]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!serviceName || !grossRevenue || !commissionRate) return;

    setLoading(true);
    await fetch("/api/calculator", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        period,
        serviceName,
        serviceType,
        grossRevenue: revenue,
        commissionRate: rate,
        rentalCost: rental,
        internetCost: internet,
        otherExpenses: other,
        notes: notes || null,
      }),
    });

    // Reset form
    setServiceName("");
    setGrossRevenue("");
    setCommissionRate("");
    setRentalCost("");
    setInternetCost("");
    setOtherExpenses("");
    setNotes("");
    setLoading(false);
    fetchRecords();
  };

  const handleDelete = async (id: string) => {
    await fetch(`/api/calculator?id=${id}`, { method: "DELETE" });
    fetchRecords();
  };

  // Summary
  const totalRevenue = records.reduce((s, r) => s + r.grossRevenue, 0);
  const totalCommission = records.reduce((s, r) => s + r.commissionAmount, 0);
  const totalExpenses = records.reduce(
    (s, r) => s + r.rentalCost + r.internetCost + r.otherExpenses,
    0
  );
  const totalProfit = records.reduce((s, r) => s + r.netProfit, 0);

  const fmt = (n: number) =>
    n.toLocaleString("ko-KR", { style: "currency", currency: "KRW" });

  return (
    <div className="max-w-6xl">
      <h1 className="text-3xl font-bold mb-2">정산계산기</h1>
      <p className="text-muted-foreground mb-6">
        서비스별 수수료율과 비용을 입력하여 순수익을 계산합니다
      </p>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              총 매출
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{fmt(totalRevenue)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              총 수수료
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-orange-600">
              {fmt(totalCommission)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              총 비용
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-red-600">
              {fmt(totalExpenses)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              순수익
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p
              className={`text-2xl font-bold ${
                totalProfit >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {fmt(totalProfit)}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Form */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>새 정산 항목</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label htmlFor="period">정산 기간</Label>
                <Input
                  id="period"
                  type="month"
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="serviceName">서비스명</Label>
                <Input
                  id="serviceName"
                  placeholder="예: KT 인터넷, 정수기 렌탈"
                  value={serviceName}
                  onChange={(e) => setServiceName(e.target.value)}
                  required
                />
              </div>

              <div>
                <Label htmlFor="serviceType">서비스 유형</Label>
                <Select value={serviceType} onValueChange={(v) => v && setServiceType(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="internet">인터넷</SelectItem>
                    <SelectItem value="rental">렌탈</SelectItem>
                    <SelectItem value="general">일반</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="grossRevenue">총 매출 (원)</Label>
                <Input
                  id="grossRevenue"
                  type="number"
                  placeholder="0"
                  value={grossRevenue}
                  onChange={(e) => setGrossRevenue(e.target.value)}
                  required
                />
              </div>

              <div>
                <Label htmlFor="commissionRate">수수료율 (%)</Label>
                <Input
                  id="commissionRate"
                  type="number"
                  step="0.1"
                  placeholder="예: 30"
                  value={commissionRate}
                  onChange={(e) => setCommissionRate(e.target.value)}
                  required
                />
              </div>

              <div>
                <Label htmlFor="rentalCost">렌탈 비용 (원)</Label>
                <Input
                  id="rentalCost"
                  type="number"
                  placeholder="0"
                  value={rentalCost}
                  onChange={(e) => setRentalCost(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="internetCost">인터넷 비용 (원)</Label>
                <Input
                  id="internetCost"
                  type="number"
                  placeholder="0"
                  value={internetCost}
                  onChange={(e) => setInternetCost(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="otherExpenses">기타 비용 (원)</Label>
                <Input
                  id="otherExpenses"
                  type="number"
                  placeholder="0"
                  value={otherExpenses}
                  onChange={(e) => setOtherExpenses(e.target.value)}
                />
              </div>

              <div>
                <Label htmlFor="notes">메모</Label>
                <Textarea
                  id="notes"
                  placeholder="추가 메모"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                />
              </div>

              {/* Live Preview */}
              {revenue > 0 && (
                <div className="p-3 rounded-lg bg-muted text-sm space-y-1">
                  <p>수수료: {fmt(commissionAmount)}</p>
                  <p className="font-bold">
                    예상 순수익:{" "}
                    <span
                      className={
                        netProfit >= 0 ? "text-green-600" : "text-red-600"
                      }
                    >
                      {fmt(netProfit)}
                    </span>
                  </p>
                </div>
              )}

              <Button type="submit" className="w-full" disabled={loading}>
                <Plus className="h-4 w-4 mr-2" />
                추가
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Records Table */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>정산 내역</CardTitle>
              <div className="flex items-center gap-2">
                <Input
                  type="month"
                  value={filterPeriod}
                  onChange={(e) => setFilterPeriod(e.target.value)}
                  className="w-40"
                  placeholder="전체 기간"
                />
                {filterPeriod && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setFilterPeriod("")}
                  >
                    초기화
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {records.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                정산 내역이 없습니다
              </p>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>기간</TableHead>
                      <TableHead>서비스명</TableHead>
                      <TableHead className="text-right">매출</TableHead>
                      <TableHead className="text-right">수수료율</TableHead>
                      <TableHead className="text-right">수수료</TableHead>
                      <TableHead className="text-right">비용</TableHead>
                      <TableHead className="text-right">순수익</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {records.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell className="whitespace-nowrap">
                          {record.period}
                        </TableCell>
                        <TableCell>{record.serviceName}</TableCell>
                        <TableCell className="text-right">
                          {fmt(record.grossRevenue)}
                        </TableCell>
                        <TableCell className="text-right">
                          {(record.commissionRate * 100).toFixed(1)}%
                        </TableCell>
                        <TableCell className="text-right text-orange-600">
                          {fmt(record.commissionAmount)}
                        </TableCell>
                        <TableCell className="text-right text-red-600">
                          {fmt(
                            record.rentalCost +
                              record.internetCost +
                              record.otherExpenses
                          )}
                        </TableCell>
                        <TableCell
                          className={`text-right font-medium ${
                            record.netProfit >= 0
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          {fmt(record.netProfit)}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(record.id)}
                          >
                            <Trash2 className="h-4 w-4 text-muted-foreground" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
