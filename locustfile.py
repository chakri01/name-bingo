from locust import HttpUser, task, between, events
import uuid
import random

class BingoPlayer(HttpUser):
    """Simulates a real player in the bingo game"""
    wait_time = between(2, 4)  # Wait 2-4 seconds between actions (matches your polling)
    
    def on_start(self):
        """
        This runs ONCE when user joins (like scanning QR code)
        Registers the player and gets their ticket
        """
        player_name = f"TestPlayer_{uuid.uuid4().hex[:8]}"
        
        try:
            response = self.client.post("/api/register", json={
                "player_name": player_name
            }, timeout=10, name="1. Registration")
            
            if response.status_code == 200:
                data = response.json()
                self.ticket_id = data.get("ticket_id")
                self.player_name = player_name
                print(f"✅ {player_name} joined the game!")
            else:
                print(f"❌ Registration failed: {response.status_code}")
                self.ticket_id = None
                # Don't quit - let test continue to see system behavior
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            self.ticket_id = None
    
    @task(10)
    def poll_game_status(self):
        """
        MOST IMPORTANT TEST - This happens constantly
        Every player checks game status every 2-4 seconds
        Weight: 10 = This happens 10x more than other tasks
        """
        if not self.ticket_id:
            return
            
        self.client.get("/api/game-status", name="2. Poll Game Status")
    
    @task(3)
    def get_ticket_data(self):
        """
        Players occasionally refresh their ticket
        Weight: 3 = Happens less frequently than polling
        """
        if not self.ticket_id:
            return
            
        self.client.get(f"/api/ticket/{self.ticket_id}", name="3. Get Ticket")
    
    @task(1)
    def attempt_claim(self):
        """
        Very rare - only happens when player thinks they won
        Weight: 1 = Happens rarely
        Only 2% of these requests actually submit claim (to avoid spam)
        """
        if not self.ticket_id:
            return
        
        if random.random() < 0.02:  # Only 2% actually claim
            response = self.client.post("/api/claim", json={
                "ticket_id": self.ticket_id
            }, name="4. Claim Win", catch_response=True)
            
            try:
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        print(f"🎉 {self.player_name} submitted a claim!")
                        response.success()
                    else:
                        # Expected: "Claim in progress" or "Invalid ticket"
                        response.success()
                else:
                    response.failure(f"Unexpected error: {response.status_code}")
            except:
                response.failure("Failed to parse response")


# Statistics and reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "="*80)
    print("🎮 BINGO LOAD TEST - 100 CONCURRENT PLAYERS")
    print("="*80)
    print(f"Backend: {environment.host}")
    print(f"Test Plan:")
    print(f"  - 100 players will join over 10 seconds (like QR scanning)")
    print(f"  - Each player polls every 2-4 seconds")
    print(f"  - Test will run until you stop it (let it run 3-5 minutes)")
    print(f"\nWhat we're testing:")
    print(f"  ✓ Can 100 people register quickly?")
    print(f"  ✓ Can system handle 100 people polling simultaneously?")
    print(f"  ✓ Response times stay under 500ms?")
    print(f"  ✓ Zero failures?")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "="*80)
    print("🏁 TEST RESULTS")
    print("="*80)
    
    stats = environment.stats
    total_requests = stats.total.num_requests
    total_failures = stats.total.num_failures
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
    
    # Overall statistics
    print(f"\n📊 OVERALL STATS:")
    print(f"   Total Requests: {total_requests:,}")
    print(f"   Failed Requests: {total_failures:,}")
    print(f"   Failure Rate: {failure_rate:.2f}%")
    print(f"   Requests/Second: {stats.total.total_rps:.2f}")
    
    # Response time statistics
    print(f"\n⏱️  RESPONSE TIMES:")
    print(f"   Average: {stats.total.avg_response_time:.0f}ms")
    print(f"   Median: {stats.total.median_response_time:.0f}ms")
    print(f"   95th Percentile: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"   99th Percentile: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print(f"   Max: {stats.total.max_response_time:.0f}ms")
    
    # Per-endpoint breakdown
    print(f"\n📋 BREAKDOWN BY ENDPOINT:")
    for name, entry in stats.entries.items():
        if entry.num_requests > 0:
            endpoint_fail_rate = (entry.num_failures / entry.num_requests * 100)
            print(f"   {name}:")
            print(f"      Requests: {entry.num_requests:,} | Failures: {entry.num_failures} ({endpoint_fail_rate:.1f}%)")
            print(f"      Avg Time: {entry.avg_response_time:.0f}ms | Max: {entry.max_response_time:.0f}ms")
    
    # Pass/Fail verdict
    print(f"\n" + "="*80)
    print("🎯 VERDICT:")
    
    passed = True
    issues = []
    
    if failure_rate >= 5:
        passed = False
        issues.append(f"❌ Failure rate too high: {failure_rate:.2f}% (target: <5%)")
    else:
        print(f"✅ Failure rate OK: {failure_rate:.2f}%")
    
    if stats.total.avg_response_time >= 500:
        passed = False
        issues.append(f"❌ Response time too slow: {stats.total.avg_response_time:.0f}ms (target: <500ms)")
    else:
        print(f"✅ Response time OK: {stats.total.avg_response_time:.0f}ms")
    
    if stats.total.get_response_time_percentile(0.95) >= 1000:
        passed = False
        issues.append(f"⚠️  95th percentile slow: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    else:
        print(f"✅ 95th percentile OK: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    
    print("\n" + "-"*80)
    if passed:
        print("🎉 TEST PASSED - Your system is ready for 100 concurrent users!")
        print("   You can confidently run your bingo game with 100 people.")
    else:
        print("⚠️  TEST FAILED - System needs optimization")
        for issue in issues:
            print(f"   {issue}")
        print("\n   Recommendations:")
        print("   - Upgrade Railway plan for more CPU/Memory")
        print("   - Increase polling interval to 4-6 seconds")
        print("   - Optimize database queries")
    
    print("="*80 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests in real-time"""
    if response_time > 1000:  # If request takes more than 1 second
        print(f"⚠️  SLOW REQUEST: {name} took {response_time:.0f}ms")