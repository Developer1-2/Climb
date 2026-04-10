Update User model:

Add field:

* receipt_count (Integer, default 0)

---

Create new endpoint:

POST /receipts/increment

Request:
{
"user_id": int
}

Logic:

* Find user
* Increment receipt_count by 1
* Return updated count

---

Create endpoint:

GET /users/{user_id}

Return:
{
"receipt_count": int,
"is_paid": boolean
}
