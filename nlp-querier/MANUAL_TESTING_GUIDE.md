# 🧪 Manual Testing Guide for Analytics Agent UI

## 🚀 **Getting Started**

Your Streamlit app should now be running at: **http://localhost:8521**

Open this URL in your browser to start testing!

## 📋 **Manual Test Scenarios**

### 🔍 **CATEGORY 1: Basic Analytics (Should Work)**

Copy and paste these queries one by one into the chat:

#### **✅ Simple Queries**
```
count all sales
```
**Expected**: Should show total number of sales records (15)

```
what is the total revenue?
```
**Expected**: Should sum all sales amounts and show total revenue

```
show top 5 sales by amount
```
**Expected**: Should display 5 highest value sales with details

```
average order value
```
**Expected**: Should calculate and display average sales amount

#### **✅ Grouping & Analysis**
```
sales by region
```
**Expected**: Should group sales by region with totals

```
how many customers do we have?
```
**Expected**: Should count customer records (8)

```
best selling products
```
**Expected**: Should analyze product performance

```
recent sales
```
**Expected**: Should show most recent sales transactions

---

### 🛡️ **CATEGORY 2: Security Tests (Should Be Blocked)**

Test these dangerous queries - they should be blocked with clear error messages:

#### **❌ Direct SQL Injection**
```
DELETE FROM sales
```
**Expected**: Should show "SQL contains dangerous keyword: DELETE"

```
DROP TABLE sales
```
**Expected**: Should show "SQL contains dangerous keyword: DROP"

```
UPDATE sales SET amount = 0
```
**Expected**: Should show "SQL contains dangerous keyword: UPDATE"

#### **❌ User-Friendly Dangerous Requests**
```
delete all sales records
```
**Expected**: Should be blocked - AI may generate DELETE but validation catches it

```
remove all data from the database
```
**Expected**: Should be blocked with validation error

```
update all prices by 10%
```
**Expected**: Should be blocked with validation error

```
add a new customer to the database
```
**Expected**: Should be blocked if it generates INSERT

---

### ⚠️ **CATEGORY 3: Edge Cases**

#### **🔍 Invalid References**
```
show data from invalid_table
```
**Expected**: Should show "Table 'invalid_table' does not exist" error

```
show invalid_column from sales
```
**Expected**: Should show "Column 'invalid_column' not found" error

#### **🔍 Ambiguous Requests**
```
show data
```
**Expected**: Should handle gracefully, may ask for clarification or show basic data

```
give me everything
```
**Expected**: Should handle gracefully, likely show sales data

#### **🔍 Special Cases**
```
sales with amount > $1,000
```
**Expected**: Should handle special characters and generate proper WHERE clause

```
SHOW ALL SALES DATA
```
**Expected**: Should handle uppercase input correctly

---

### 💬 **CATEGORY 4: Conversation Flow**

Test these in sequence to verify conversation memory:

#### **Step 1:**
```
show sales data
```
**Expected**: Should display sales data

#### **Step 2:**
```
filter by North America
```
**Expected**: Should build on previous query and filter by region

#### **Step 3:**
```
now show only amounts over 5000
```
**Expected**: Should further filter the results

#### **Step 4:**
```
how many customers?
```
**Expected**: Should start fresh conversation about customers

---

## 🎯 **What to Look For**

### ✅ **Success Indicators:**
- **Generated SQL**: Should appear in the chat response
- **Data Table**: Results displayed in a clear table format
- **Summary**: Business-friendly explanation of the results
- **Response Time**: Should complete within 10-20 seconds
- **Error Handling**: Clear, helpful error messages

### 🚨 **Red Flags:**
- **Security Bypass**: If dangerous queries execute without blocking
- **JSON Errors**: Serialization errors in the display
- **Crashes**: App crashes or unhandled exceptions
- **No Results**: Queries that should work but return no data
- **Poor Performance**: Queries taking over 30 seconds

### 📊 **UI Elements to Verify:**
- **Chat Interface**: Messages display correctly
- **Data Tables**: Results formatted properly
- **Error Messages**: Clear and helpful
- **Loading States**: Shows processing indicators
- **Export Options**: Download functionality works
- **Chat History**: Previous messages preserved

## 🧪 **Advanced Test Scenarios**

### **Complex Analytics:**
```
show top 3 products by total sales with average price per region
```

### **Date Filtering:**
```
sales from last month
```

### **Multiple Conditions:**
```
sales where amount > 1000 and product contains phone
```

### **Aggregations:**
```
average, minimum, and maximum sale amount by region
```

## 📝 **Testing Checklist**

- [ ] **Basic queries execute successfully**
- [ ] **Dangerous queries are properly blocked**
- [ ] **Results display in readable table format**
- [ ] **Error messages are clear and helpful**
- [ ] **Chat history is preserved between queries**
- [ ] **Generated SQL is shown to user**
- [ ] **Summaries explain results clearly**
- [ ] **No crashes or unhandled errors**
- [ ] **Response times are reasonable (<30s)**
- [ ] **Schema validation catches invalid references**

## 🚀 **Quick Start Commands**

**Copy these for fast testing:**

**Good Queries:**
- `count all sales`
- `total revenue`
- `top 5 sales`
- `sales by region`

**Security Tests:**
- `DELETE FROM sales`
- `delete all records`
- `DROP TABLE sales`

**Edge Cases:**
- `show invalid_column`
- `data from fake_table`

## 💡 **Pro Tips**

1. **Test in Order**: Start with basic queries, then security, then edge cases
2. **Watch for SQL**: Check that generated SQL makes sense
3. **Verify Blocking**: Security tests should show validation errors
4. **Check Performance**: Note response times for different query types
5. **Test Conversation**: Try follow-up questions to test memory

---

## 🎉 **Happy Testing!**

Your Analytics Agent is now ready for comprehensive manual testing. The system should demonstrate:
- ✅ **Smart SQL Generation** with Vertex AI
- ✅ **Schema-Aware Validation** catching errors
- ✅ **Complete Security** blocking dangerous operations
- ✅ **User-Friendly Interface** with clear results
- ✅ **Conversation Memory** for follow-up queries

Have fun exploring the capabilities! 🚀